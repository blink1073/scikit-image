#!/bin/bash
# Set up ccache for emscripten builds.
#
# 1. Fixes the mtime of .emscripten to epoch 0 so ccache sees a stable
#    compiler fingerprint (emsdk recreates it on every activation).
# 2. Creates /tmp/ccache-clang-wrapper, the EM_COMPILER_WRAPPER script that
#    normalizes emscripten's random /tmp/tmpXXX.c temp files to content-hash-
#    based stable paths so ccache hits across CI runs.
set -euo pipefail

emcc=$(which emcc)

# Mirror emcc's config-file search order (emscripten/tools/config.py)
emscripten_root=$(dirname "$emcc")
emsdk_root=$(dirname "$(dirname "$emscripten_root")")
if [[ -f "$emscripten_root/.emscripten" ]]; then
    em_config="$emscripten_root/.emscripten"
elif [[ -f "$emsdk_root/.emscripten" ]]; then
    em_config="$emsdk_root/.emscripten"
else
    em_config="$HOME/.emscripten"
fi

echo "Fixing mtime of $em_config"
touch -d @0 "$em_config"

# Create the EM_COMPILER_WRAPPER. Emscripten calls it as:
#   <wrapper> <clang_path> [clang_args...]
#
# Replaces /tmp/tmpXXX.c (random name) with /tmp/ccache-src/<sha256>.c so
# ccache sees a stable, content-derived path rather than a random one.
mkdir -p /tmp/ccache-src
cat > /tmp/ccache-clang-wrapper << 'WRAPPER'
#!/bin/bash
clang="$1"
shift
args=("$@")
for i in "${!args[@]}"; do
    if [[ "${args[$i]}" == "-c" ]]; then
        src="${args[$((i+1))]:-}"
        if [[ "$src" == /tmp/tmp*.c && -f "$src" ]]; then
            hash=$(sha256sum "$src" | cut -c1-64)
            stable="/tmp/ccache-src/${hash}.c"
            [[ -f "$stable" ]] || cp "$src" "$stable"
            args[$((i+1))]="$stable"
        fi
        break
    fi
done
exec ccache "$clang" "${args[@]}"
WRAPPER
chmod +x /tmp/ccache-clang-wrapper
echo "Created EM_COMPILER_WRAPPER: /tmp/ccache-clang-wrapper"
