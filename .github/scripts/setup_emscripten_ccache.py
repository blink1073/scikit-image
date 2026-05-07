#!/usr/bin/env python3
"""Set up ccache for emscripten builds.

Creates a ccache wrapper for emcc so that ccache sees the original source
file paths (not emscripten's internal temp files with random names). Also
fixes the mtime of the emscripten config file to prevent ccache misses.

Background: when EM_COMPILER_WRAPPER=ccache is used, emscripten preprocesses
source files to /tmp/tmpXXX.c temp files with random names before calling
clang. ccache then hashes those random names, causing misses every run. By
wrapping emcc itself (before the temp files are created), ccache sees the
original stable source paths.
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

# Create a ccache wrapper for emcc so ccache sees the original source file
# paths rather than emscripten's internal temp files. The wrapper must use an
# absolute path to the real emcc to avoid infinite recursion (the wrapper dir
# is prepended to PATH by CIBW_ENVIRONMENT).
wrapper_dir = pathlib.Path("/tmp/emcc-wrapper")
wrapper_dir.mkdir(exist_ok=True)
wrapper = wrapper_dir / "emcc"
wrapper.write_text(f"#!/bin/bash\nexec ccache {emcc} \"$@\"\n")
wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print(f"Created emcc wrapper: {wrapper} -> ccache {emcc}")
