#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
source "${IPYCALC_VERSIONS_FILE:-$SCRIPT_DIR/versions.env}"

APP_VERSION=$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$PROJECT_ROOT/pyproject.toml" | head -1)
BUILD_ROOT=${IPYCALC_BUILD_ROOT:-$PROJECT_ROOT/build}
APPDIR=$BUILD_ROOT/IPyCalc.AppDir
DOWNLOAD_DIR=$BUILD_ROOT/downloads
DIST_DIR=${IPYCALC_DIST_DIR:-$PROJECT_ROOT/dist}
APPDIR_ONLY=0
DOWNLOADS_ONLY=0

if [[ ${1:-} == "--appdir-only" ]]; then
    APPDIR_ONLY=1
elif [[ ${1:-} == "--downloads-only" ]]; then
    DOWNLOADS_ONLY=1
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--appdir-only|--downloads-only]" >&2
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
        KITTY_ASSET_ARCH=x86_64
        APPIMAGETOOL_ASSET=appimagetool-x86_64.AppImage
        ;;
    aarch64|arm64)
        ARCH=aarch64
        KITTY_URL=$KITTY_AARCH64_URL
        KITTY_SHA256=$KITTY_AARCH64_SHA256
        APPIMAGETOOL_URL=$APPIMAGETOOL_AARCH64_URL
        APPIMAGETOOL_SHA256=$APPIMAGETOOL_AARCH64_SHA256
        RUNTIME_URL=$APPIMAGE_RUNTIME_AARCH64_URL
        RUNTIME_SHA256=$APPIMAGE_RUNTIME_AARCH64_SHA256
        KITTY_ASSET_ARCH=arm64
        APPIMAGETOOL_ASSET=appimagetool-aarch64.AppImage
        ;;
    *)
        echo "Unsupported architecture: ${IPYCALC_ARCH:-$(uname -m)}" >&2
        exit 1
        ;;
esac

mkdir -p "$DOWNLOAD_DIR" "$DIST_DIR"

download_verified() {
    local url=$1
    local destination=$2
    local checksum=$3
    local temporary=$destination.part
    if [[ -f $destination ]]; then
        if verify "$checksum" "$destination"; then
            return
        fi
        echo "Checksum mismatch: $destination" >&2
        exit 1
    fi
    rm -f -- "$temporary"
    curl --fail --location --output "$temporary" "$url"
    if ! verify "$checksum" "$temporary"; then
        rm -f -- "$temporary"
        echo "Downloaded file checksum mismatch: $destination" >&2
        exit 1
    fi
    mv -- "$temporary" "$destination"
    printf '%s\n' "$checksum" > "$destination.sha256"
}

verify() {
    local checksum=$1
    local path=$2
    printf '%s  %s\n' "$checksum" "$path" | sha256sum --check --status
}

read_checksum() {
    local path=$1
    local checksum_file=$path.sha256
    local checksum
    [[ -f $checksum_file ]] || return 1
    IFS= read -r checksum < "$checksum_file" || return 1
    [[ $checksum =~ ^[[:xdigit:]]{64}$ ]] || return 1
    printf '%s\n' "$checksum"
}

version_is_newer() {
    local candidate=$1
    local existing=$2
    [[ $candidate != "$existing" ]] && [[ $(printf '%s\n%s\n' "$existing" "$candidate" | sort -V | tail -1) == "$candidate" ]]
}

json_value() {
    local key=$1
    sed -n "s/^[[:space:]]*\"$key\": \"\([^\"]*\)\".*/\1/p" | head -1
}

json_asset_value() {
    local asset=$1
    local key=$2
    awk -v asset="$asset" -v key="$key" '
        index($0, "\"name\": \"") {
            if (found) exit
            if (index($0, "\"name\": \"" asset "\"")) found = 1
        }
        found && index($0, "\"" key "\": \"") {
            sub("^.*\"" key "\": \"", "")
            sub("\".*$", "")
            print
            exit
        }
    '
}

select_cached_kitty() {
    local path base version checksum
    local pinned=$DOWNLOAD_DIR/kitty-$KITTY_VERSION-$ARCH.txz
    KITTY_ARCHIVE=""
    SELECTED_KITTY_VERSION=""
    shopt -s nullglob
    for path in "$DOWNLOAD_DIR"/kitty-*-$ARCH.txz; do
        base=${path##*/}
        version=${base#kitty-}
        version=${version%-$ARCH.txz}
        if [[ $path == "$pinned" ]]; then
            checksum=$KITTY_SHA256
        else
            checksum=$(read_checksum "$path") || continue
        fi
        if ! verify "$checksum" "$path"; then
            echo "Ignoring cached Kitty with a bad checksum: $path" >&2
            continue
        fi
        if [[ -z $SELECTED_KITTY_VERSION ]] || version_is_newer "$version" "$SELECTED_KITTY_VERSION"; then
            KITTY_ARCHIVE=$path
            SELECTED_KITTY_VERSION=$version
        fi
    done
    shopt -u nullglob
}

select_cached_appimagetool() {
    local path checksum release
    local pinned=$DOWNLOAD_DIR/appimagetool-$APPIMAGETOOL_VERSION-$ARCH.AppImage
    APPIMAGETOOL=""
    SELECTED_APPIMAGETOOL_DATE=""
    shopt -s nullglob
    for path in "$DOWNLOAD_DIR"/appimagetool-*-$ARCH.AppImage; do
        if [[ $path == "$pinned" ]]; then
            checksum=$APPIMAGETOOL_SHA256
            release=$APPIMAGETOOL_UPDATED_AT
        else
            checksum=$(read_checksum "$path") || continue
            [[ -f $path.release ]] || continue
            IFS= read -r release < "$path.release" || continue
        fi
        if ! verify "$checksum" "$path"; then
            echo "Ignoring cached appimagetool with a bad checksum: $path" >&2
            continue
        fi
        if [[ -z $SELECTED_APPIMAGETOOL_DATE || $release > $SELECTED_APPIMAGETOOL_DATE ]]; then
            APPIMAGETOOL=$path
            SELECTED_APPIMAGETOOL_DATE=$release
        fi
    done
    shopt -u nullglob
}

refresh_requested() {
    case ${IPYCALC_REFRESH_DOWNLOADS:-ask} in
        always|yes|1)
            return 0
            ;;
        never|no|0)
            return 1
            ;;
        ask)
            if [[ ! -t 0 || ! -t 1 ]]; then
                return 1
            fi
            local answer
            local targets="Kitty and appimagetool"
            if [[ $APPDIR_ONLY -eq 1 ]]; then
                targets="Kitty"
            fi
            read -r -p "Check for newer $targets downloads? [y/N] " answer
            [[ $answer == [yY] || $answer == [yY][eE][sS] ]]
            ;;
        *)
            echo "IPYCALC_REFRESH_DOWNLOADS must be ask, always, or never." >&2
            exit 2
            ;;
    esac
}

refresh_kitty() {
    [[ -z ${IPYCALC_KITTY_ARCHIVE:-} ]] || return
    local latest release_json asset digest url destination
    latest=$(curl --fail --silent --show-error "${IPYCALC_KITTY_VERSION_URL:-https://sw.kovidgoyal.net/kitty/current-version.txt}") || {
        echo "Could not check the newest Kitty version. Using the cached or pinned version." >&2
        return
    }
    latest=${latest//$'\r'/}
    latest=${latest//$'\n'/}
    if [[ -n $SELECTED_KITTY_VERSION ]] && ! version_is_newer "$latest" "$SELECTED_KITTY_VERSION"; then
        echo "Cached Kitty $SELECTED_KITTY_VERSION is current."
        return
    fi
    asset=kitty-$latest-$KITTY_ASSET_ARCH.txz
    release_json=$(curl --fail --silent --show-error "${IPYCALC_KITTY_RELEASE_API:-https://api.github.com/repos/kovidgoyal/kitty/releases/tags/v$latest}") || {
        echo "Could not read the Kitty $latest release metadata. Using the cached or pinned version." >&2
        return
    }
    digest=$(printf '%s\n' "$release_json" | json_asset_value "$asset" digest)
    url=$(printf '%s\n' "$release_json" | json_asset_value "$asset" browser_download_url)
    digest=${digest#sha256:}
    if [[ ! $digest =~ ^[[:xdigit:]]{64}$ || -z $url ]]; then
        echo "The Kitty $latest release metadata has no verified $asset asset." >&2
        return
    fi
    destination=$DOWNLOAD_DIR/kitty-$latest-$ARCH.txz
    echo "Downloading newer Kitty $latest."
    download_verified "$url" "$destination" "$digest"
    KITTY_ARCHIVE=$destination
    SELECTED_KITTY_VERSION=$latest
}

refresh_appimagetool() {
    [[ $APPDIR_ONLY -eq 0 ]] || return
    local release_json updated commit digest url destination
    release_json=$(curl --fail --silent --show-error "${IPYCALC_APPIMAGETOOL_RELEASE_API:-https://api.github.com/repos/AppImage/appimagetool/releases/latest}") || {
        echo "Could not check the newest appimagetool version. Using the cached or pinned version." >&2
        return
    }
    updated=$(printf '%s\n' "$release_json" | json_value updated_at)
    commit=$(printf '%s\n' "$release_json" | json_value target_commitish)
    if [[ -n $SELECTED_APPIMAGETOOL_DATE && ( -z $updated || $updated < $SELECTED_APPIMAGETOOL_DATE || $updated == "$SELECTED_APPIMAGETOOL_DATE" ) ]]; then
        echo "Cached appimagetool is current."
        return
    fi
    digest=$(printf '%s\n' "$release_json" | json_asset_value "$APPIMAGETOOL_ASSET" digest)
    url=$(printf '%s\n' "$release_json" | json_asset_value "$APPIMAGETOOL_ASSET" browser_download_url)
    digest=${digest#sha256:}
    if [[ -z $updated || -z $commit || ! $digest =~ ^[[:xdigit:]]{64}$ || -z $url ]]; then
        echo "The appimagetool release metadata has no verified $APPIMAGETOOL_ASSET asset." >&2
        return
    fi
    destination=$DOWNLOAD_DIR/appimagetool-continuous-${commit:0:8}-$ARCH.AppImage
    echo "Downloading newer appimagetool build ${commit:0:8}."
    download_verified "$url" "$destination" "$digest"
    printf '%s\n' "$updated" > "$destination.release"
    APPIMAGETOOL=$destination
    SELECTED_APPIMAGETOOL_DATE=$updated
}

if [[ -n ${IPYCALC_KITTY_ARCHIVE:-} ]]; then
    KITTY_ARCHIVE=$IPYCALC_KITTY_ARCHIVE
    if ! verify "$KITTY_SHA256" "$KITTY_ARCHIVE"; then
        echo "Kitty checksum mismatch: $KITTY_ARCHIVE" >&2
        exit 1
    fi
    SELECTED_KITTY_VERSION=$KITTY_VERSION
else
    select_cached_kitty
fi

if [[ $APPDIR_ONLY -eq 0 ]]; then
    select_cached_appimagetool
else
    APPIMAGETOOL=""
fi

if refresh_requested; then
    refresh_kitty
    refresh_appimagetool
fi

if [[ -z $KITTY_ARCHIVE ]]; then
    KITTY_ARCHIVE=$DOWNLOAD_DIR/kitty-$KITTY_VERSION-$ARCH.txz
    download_verified "$KITTY_URL" "$KITTY_ARCHIVE" "$KITTY_SHA256"
    SELECTED_KITTY_VERSION=$KITTY_VERSION
fi
echo "Using Kitty $SELECTED_KITTY_VERSION from $KITTY_ARCHIVE"

RUNTIME=$DOWNLOAD_DIR/runtime-$APPIMAGE_RUNTIME_VERSION-$ARCH
if [[ $APPDIR_ONLY -eq 0 ]]; then
    if [[ -z $APPIMAGETOOL ]]; then
        APPIMAGETOOL=$DOWNLOAD_DIR/appimagetool-$APPIMAGETOOL_VERSION-$ARCH.AppImage
        download_verified "$APPIMAGETOOL_URL" "$APPIMAGETOOL" "$APPIMAGETOOL_SHA256"
        SELECTED_APPIMAGETOOL_DATE=$APPIMAGETOOL_UPDATED_AT
    fi
    echo "Using appimagetool from $APPIMAGETOOL"
    download_verified "$RUNTIME_URL" "$RUNTIME" "$RUNTIME_SHA256"
fi

if [[ $DOWNLOADS_ONLY -eq 1 ]]; then
    echo "Downloads are ready in $DOWNLOAD_DIR"
    exit 0
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

chmod u+x "$APPIMAGETOOL"

OUTPUT=$DIST_DIR/IPyCalc-$APP_VERSION-$ARCH.AppImage
ARCH=$ARCH APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" --runtime-file "$RUNTIME" "$APPDIR" "$OUTPUT"
echo "AppImage created at $OUTPUT"
