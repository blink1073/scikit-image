#!/usr/bin/env python3
"""Download scikit-image's example datasets without any third-party dependencies.

This is a fallback for environments that can't or don't want to depend on
``pooch`` (e.g. Linux distribution packaging). It downloads every data file
that scikit-image's public ``skimage.data`` functions can fetch, verifying
each file's sha256 hash against the registry in
``src/_skimage2/data/_registry.py``.

Note: this does not download files used only internally by scikit-image's
test suite (files with no entry in ``registry_urls``); those are fetched
directly from the scikit-image GitHub repository by the test runner and are
not needed to use the public ``skimage.data`` API.
"""

import argparse
import ast
import concurrent.futures
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REGISTRY_PATH = _HERE.parent / 'src' / '_skimage2' / 'data' / '_registry.py'


def _load_registry():
    """Parse ``registry``/``registry_urls`` out of ``_registry.py``.

    Only evaluates simple top-level ``name = <expr>`` assignments (building
    up a namespace of just those names as it goes, e.g. so an f-string like
    ``registry_urls``'s values can reference an already-assigned URL
    constant) -- any other statement (imports, function/class defs, etc.) is
    skipped rather than executed, so this keeps working even if the registry
    module gains code unrelated to the two dicts this script needs.
    """
    source = _REGISTRY_PATH.read_text()
    tree = ast.parse(source, filename=str(_REGISTRY_PATH))

    namespace = {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        expr = ast.fix_missing_locations(ast.Expression(node.value))
        code = compile(expr, str(_REGISTRY_PATH), 'eval')
        namespace[target.id] = eval(code, {'__builtins__': {}}, namespace)  # noqa: S307

    return namespace['registry'], namespace['registry_urls']


def _file_hash(path, chunk_size=65536):
    hasher = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download_one(data_filename, url, expected_hash, dest_dir, force):
    dest_path = dest_dir / data_filename
    if not force and dest_path.exists() and _file_hash(dest_path) == expected_hash:
        return data_filename, 'cached', None

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(f'{dest_path}.part')
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with open(tmp_path, 'wb') as fh:
                while chunk := response.read(65536):
                    fh.write(chunk)
    except (urllib.error.URLError, TimeoutError) as err:
        tmp_path.unlink(missing_ok=True)
        return data_filename, 'error', str(err)

    actual_hash = _file_hash(tmp_path)
    if actual_hash != expected_hash:
        tmp_path.unlink(missing_ok=True)
        return (
            data_filename,
            'error',
            f'hash mismatch (expected {expected_hash}, got {actual_hash})',
        )

    tmp_path.replace(dest_path)
    return data_filename, 'downloaded', None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dest',
        required=True,
        type=Path,
        help='Directory to download data files into '
        '(mirrors the layout skimage.data expects).',
    )
    parser.add_argument(
        '--jobs', type=int, default=8, help='Number of parallel downloads (default: 8).'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-download files even if a correctly-hashed copy already exists.',
    )
    args = parser.parse_args(argv)

    registry, registry_urls = _load_registry()
    skipped = sorted(set(registry) - set(registry_urls))
    missing_hash = sorted(set(registry_urls) - set(registry))
    if missing_hash:
        print(
            f'WARNING: {len(missing_hash)} registry_urls entr'
            f'{"y" if len(missing_hash) == 1 else "ies"} with no matching hash '
            f'in registry, skipping: {", ".join(missing_hash)}',
            file=sys.stderr,
        )

    args.dest.mkdir(parents=True, exist_ok=True)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(_download_one, key, url, registry[key], args.dest, args.force)
            for key, url in registry_urls.items()
            if key in registry
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    downloaded = [r for r in results if r[1] == 'downloaded']
    cached = [r for r in results if r[1] == 'cached']
    errors = [r for r in results if r[1] == 'error']

    print(
        f'{len(downloaded)} downloaded, {len(cached)} already cached, {len(errors)} failed'
    )
    if skipped:
        print(
            f'{len(skipped)} test-only fixtures skipped (not part of the public '
            'skimage.data API; fetched by the test suite from GitHub directly)'
        )
    for key, _status, err in errors:
        print(f'  FAILED {key}: {err}', file=sys.stderr)

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
