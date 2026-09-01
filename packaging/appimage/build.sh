#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
source "$SCRIPT_DIR/versions.env"

APP_VERSION=$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$PROJECT_ROOT/pyproject.toml" | head -1)
BUILD_ROOT=${IPYCALC_BUILD_ROOT:-$PROJECT_ROOT/build}
APPDIR=$BUILD_ROOT/IPyCalc.AppDir
DOWNLOAD_DIR=$BUILD_ROOT/downloads
DIST_DIR=${IPYCALC_DIST_DIR:-$PROJECT_ROOT/dist}
APPDIR_ONLY=0

if [[ ${1:-} == "--appdir-only" ]]; then
    APPDIR_ONLY=1
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--appdir-only]" >&2
    exit 2
fi

case ${IPYCALC_ARCH:-$(uname -m)} in
    x86_64|amd64)
        ARCH=x86_64
        KITTY_URL=$KITTY_X86_64_URL
        KITTY_SHA256=$KITTY_X86_64_SHA256
        APPIMAGETOOL_URL=$APPIMAGETOOL_X86_64_URL
        APPIMAGETOOL_SHA256=$APPIMAGETOOL_X86_64_SHA256
        RUNTIME_URL=$APPIMAGE_RUNTIME_X86_64_URL
        RUNTIME_SHA256=$APPIMAGE_RUNTIME_X86_64_SHA256
        ;;
    aarch64|arm64)
        ARCH=aarch64
        KITTY_URL=$KITTY_AARCH64_URL
        KITTY_SHA256=$KITTY_AARCH64_SHA256
        APPIMAGETOOL_URL=$APPIMAGETOOL_AARCH64_URL
        APPIMAGETOOL_SHA256=$APPIMAGETOOL_AARCH64_SHA256
        RUNTIME_URL=$APPIMAGE_RUNTIME_AARCH64_URL
        RUNTIME_SHA256=$APPIMAGE_RUNTIME_AARCH64_SHA256
        ;;
    *)
        echo "Unsupported architecture: ${IPYCALC_ARCH:-$(uname -m)}" >&2
        exit 1
        ;;
esac

mkdir -p "$DOWNLOAD_DIR" "$DIST_DIR"

download() {
    local url=$1
    local destination=$2
    if [[ ! -f $destination ]]; then
        curl --fail --location --output "$destination" "$url"
    fi
}

verify() {
    local checksum=$1
    local path=$2
    printf '%s  %s\n' "$checksum" "$path" | sha256sum --check --status
}

KITTY_ARCHIVE=${IPYCALC_KITTY_ARCHIVE:-$DOWNLOAD_DIR/kitty-$KITTY_VERSION-$ARCH.txz}
if [[ -z ${IPYCALC_KITTY_ARCHIVE:-} ]]; then
    download "$KITTY_URL" "$KITTY_ARCHIVE"
fi
if ! verify "$KITTY_SHA256" "$KITTY_ARCHIVE"; then
    echo "Kitty checksum mismatch: $KITTY_ARCHIVE" >&2
    exit 1
fi

rm -rf -- "$APPDIR"
mkdir -p \
    "$APPDIR/opt/ipycalc" \
    "$APPDIR/usr/share/doc/ipycalc" \
    "$APPDIR/usr/bin" \
    "$APPDIR/usr/lib/kitty.app" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
    "$APPDIR/usr/share/metainfo"

tar -xf "$KITTY_ARCHIVE" -C "$APPDIR/usr/lib/kitty.app"
cp -a "$PROJECT_ROOT/src/ipycalc" "$APPDIR/opt/ipycalc/"
find "$APPDIR/opt/ipycalc" -type d -name __pycache__ -prune -exec rm -rf -- {} +
install -m 0644 "$PROJECT_ROOT/LICENSE.md" "$APPDIR/usr/share/doc/ipycalc/LICENSE.md"
install -m 0644 "$PROJECT_ROOT/THIRD_PARTY_NOTICES.md" "$APPDIR/usr/share/doc/ipycalc/THIRD_PARTY_NOTICES.md"

install -m 0755 "$SCRIPT_DIR/AppRun" "$APPDIR/AppRun"
install -m 0644 "$SCRIPT_DIR/org.ipycalc.IPyCalc.desktop" "$APPDIR/org.ipycalc.IPyCalc.desktop"
install -m 0644 "$SCRIPT_DIR/org.ipycalc.IPyCalc.svg" "$APPDIR/org.ipycalc.IPyCalc.svg"
install -m 0644 "$SCRIPT_DIR/org.ipycalc.IPyCalc.desktop" "$APPDIR/usr/share/applications/org.ipycalc.IPyCalc.desktop"
install -m 0644 "$SCRIPT_DIR/org.ipycalc.IPyCalc.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/org.ipycalc.IPyCalc.svg"
install -m 0644 "$SCRIPT_DIR/org.ipycalc.IPyCalc.metainfo.xml" "$APPDIR/usr/share/metainfo/org.ipycalc.IPyCalc.appdata.xml"
ln -s org.ipycalc.IPyCalc.svg "$APPDIR/.DirIcon"
ln -s ../../AppRun "$APPDIR/usr/bin/ipycalc"
ln -s ../lib/kitty.app/bin/kitty "$APPDIR/usr/bin/kitty"
ln -s ../lib/kitty.app/bin/kitten "$APPDIR/usr/bin/kitten"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$APPDIR/org.ipycalc.IPyCalc.desktop"
fi

if [[ $APPDIR_ONLY -eq 1 ]]; then
    echo "AppDir created at $APPDIR"
    exit 0
fi

APPIMAGETOOL=$DOWNLOAD_DIR/appimagetool-$APPIMAGETOOL_VERSION-$ARCH.AppImage
RUNTIME=$DOWNLOAD_DIR/runtime-$APPIMAGE_RUNTIME_VERSION-$ARCH
download "$APPIMAGETOOL_URL" "$APPIMAGETOOL"
download "$RUNTIME_URL" "$RUNTIME"
if ! verify "$APPIMAGETOOL_SHA256" "$APPIMAGETOOL"; then
    echo "appimagetool checksum mismatch: $APPIMAGETOOL" >&2
    exit 1
fi
if ! verify "$RUNTIME_SHA256" "$RUNTIME"; then
    echo "AppImage runtime checksum mismatch: $RUNTIME" >&2
    exit 1
fi
chmod u+x "$APPIMAGETOOL"

OUTPUT=$DIST_DIR/IPyCalc-$APP_VERSION-$ARCH.AppImage
ARCH=$ARCH APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" --runtime-file "$RUNTIME" "$APPDIR" "$OUTPUT"
echo "AppImage created at $OUTPUT"
