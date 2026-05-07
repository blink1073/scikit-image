#!/usr/bin/env python3
"""Set up ccache for emscripten builds.

Creates a custom EM_COMPILER_WRAPPER script that normalizes emscripten's
random temp file names to content-hash-based paths so ccache sees stable
source file paths across runs. Also fixes the mtime of the emscripten config
file to prevent ccache compiler-fingerprint misses.

Background: emscripten preprocesses source files to /tmp/tmpXXX.c temp files
with random names before calling clang. When EM_COMPILER_WRAPPER=ccache is
used, ccache hashes those random names as part of the preprocessed content,
causing misses every run. Our wrapper intercepts the clang invocation and
replaces the random path with /tmp/ccache-src/<sha256>.c so ccache always
sees the same path for the same content.
"""

import os
import pathlib
import shutil
import stat
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

# Create the EM_COMPILER_WRAPPER script. Emscripten calls it as:
#   <wrapper> <clang_path> [clang_args...]
#
# The wrapper normalizes /tmp/tmpXXX.c temp files (random names created by
# emscripten before calling clang) to /tmp/ccache-src/<sha256>.c so ccache
# sees a stable, content-derived path rather than a random one.
wrapper = pathlib.Path("/tmp/ccache-clang-wrapper.py")
wrapper.write_text("""\
#!/usr/bin/env python3
import hashlib
import os
import pathlib
import sys

SRC_CACHE = pathlib.Path("/tmp/ccache-src")
SRC_CACHE.mkdir(exist_ok=True)

# argv: [this_script, clang_path, ...clang_args...]
clang = sys.argv[1]
args = list(sys.argv[2:])

# Replace random /tmp/tmpXXX.c with a content-hash-based stable path.
for i, arg in enumerate(args):
    if arg == "-c" and i + 1 < len(args):
        src = pathlib.Path(args[i + 1])
        if src.exists() and src.suffix == ".c" and src.name.startswith("tmp") and str(src).startswith("/tmp/"):
            content = src.read_bytes()
            h = hashlib.sha256(content).hexdigest()
            stable = SRC_CACHE / f"{h}.c"
            if not stable.exists():
                stable.write_bytes(content)
            args[i + 1] = str(stable)
        break

os.execvp("ccache", ["ccache", clang] + args)
""")
wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print(f"Created EM_COMPILER_WRAPPER: {wrapper}")
