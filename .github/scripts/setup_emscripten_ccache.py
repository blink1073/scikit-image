#!/usr/bin/env python3
"""Configure emscripten to use ccache by modifying the .emscripten config file.

COMPILER_WRAPPER in emscripten 4.x is a config-file key, not an env var.
We also fix the mtime to 0 so ccache sees a stable fingerprint across runs
even though emsdk recreates the file on each activation.
"""

import os
import pathlib
import shutil
import sys

emcc = shutil.which("emcc")
if not emcc:
    print("emcc not found in PATH", file=sys.stderr)
    sys.exit(1)

em_config = next(
    (
        p / ".emscripten"
        for p in pathlib.Path(emcc).parents
        if (p / ".emscripten").exists()
    ),
    None,
)
if not em_config:
    print("Could not find .emscripten config file", file=sys.stderr)
    sys.exit(1)

content = em_config.read_text()
if "COMPILER_WRAPPER" not in content:
    em_config.write_text(content + "\nCOMPILER_WRAPPER = 'ccache'\n")
    print(f"Added COMPILER_WRAPPER to {em_config}")

# Fix mtime to prevent ccache misses caused by emsdk recreating this file
os.utime(em_config, (0, 0))
print(f"Fixed mtime of {em_config}")
