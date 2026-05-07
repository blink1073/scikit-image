#!/usr/bin/env python3
"""Fix the mtime of the emscripten config file to prevent ccache misses.

Emscripten's ccache integration (EM_COMPILER_WRAPPER=ccache) hashes the
mtime of .emscripten as part of the compiler fingerprint. Since emsdk
recreates this file on every activation, we reset its mtime to a fixed
value so ccache sees a stable fingerprint across CI runs.

COMPILER_WRAPPER is set via EM_COMPILER_WRAPPER env var (not here), since
emscripten's config loader checks EM_<KEY> env vars for each CONFIG_KEY.
"""

import os
import pathlib
import shutil
import sys

emcc = shutil.which("emcc")
if not emcc:
    print("emcc not found in PATH", file=sys.stderr)
    sys.exit(1)

# Mirror emcc's own config-file search order (see emscripten/tools/config.py)
em_config_path = os.environ.get("EM_CONFIG")
if em_config_path:
    em_config = pathlib.Path(em_config_path)
else:
    # embedded_config: .emscripten next to emcc itself
    emscripten_root = pathlib.Path(emcc).parent
    embedded = emscripten_root / ".emscripten"
    # emsdk_embedded_config: two levels above emscripten root (emsdk root)
    emsdk_root = emscripten_root.parent.parent
    emsdk_embedded = emsdk_root / ".emscripten"

    if embedded.exists():
        em_config = embedded
    elif emsdk_embedded.exists():
        em_config = emsdk_embedded
    else:
        em_config = pathlib.Path.home() / ".emscripten"

if not em_config.exists():
    print(
        f"Could not find .emscripten config file (tried: {em_config})", file=sys.stderr
    )
    sys.exit(1)

print(f"Fixing mtime of {em_config}")
os.utime(em_config, (0, 0))
print(f"EM_COMPILER_WRAPPER={os.environ.get('EM_COMPILER_WRAPPER', '(not set)')}")
print(f"CCACHE_DIR={os.environ.get('CCACHE_DIR', '(not set)')}")
