#!/bin/bash
# Apply HC5661A custom board overlay into rt-n56u source tree
set -euo pipefail

ROOT="${1:-$GITHUB_WORKSPACE/rt-n56u}"
OVERLAY="$(cd "$(dirname "$0")/.." && pwd)"

echo "[prepare] overlay=$OVERLAY"
echo "[prepare] source=$ROOT"

BOARD_DST="$ROOT/trunk/configs/boards/HC5661A"
TMPL_DST="$ROOT/trunk/configs/templates"

mkdir -p "$BOARD_DST" "$TMPL_DST"

cp -f "$OVERLAY/boards/HC5661A/board.h" "$BOARD_DST/board.h"
cp -f "$OVERLAY/boards/HC5661A/board.mk" "$BOARD_DST/board.mk"
cp -f "$OVERLAY/boards/HC5661A/kernel-3.4.x.config" "$BOARD_DST/kernel-3.4.x.config"
cp -f "$OVERLAY/templates/HC5661A.config" "$TMPL_DST/HC5661A.config"

# libc: prefer shared uclibc template from upstream tree
if [ -f "$ROOT/trunk/configs/boards/uclibc-mipsel.config" ]; then
  ln -sfn ../uclibc-mipsel.config "$BOARD_DST/libc.config"
elif [ -f "$OVERLAY/boards/HC5661A/libc.config" ]; then
  cp -f "$OVERLAY/boards/HC5661A/libc.config" "$BOARD_DST/libc.config"
else
  # fallback: copy from any existing MT7628 board
  ref=$(find "$ROOT/trunk/configs/boards" -name libc.config | head -n1)
  if [ -n "$ref" ]; then
    cp -fL "$ref" "$BOARD_DST/libc.config"
  else
    echo "[prepare] ERROR: libc.config not found" >&2
    exit 1
  fi
fi

# Ensure 8MB flash Storage size (128KB) — critical for W25Q64
if grep -q '^CONFIG_MTD_STORE_PART_SIZ=' "$BOARD_DST/kernel-3.4.x.config"; then
  sed -i 's/^CONFIG_MTD_STORE_PART_SIZ=.*/CONFIG_MTD_STORE_PART_SIZ=0x20000/' \
    "$BOARD_DST/kernel-3.4.x.config"
else
  echo 'CONFIG_MTD_STORE_PART_SIZ=0x20000' >> "$BOARD_DST/kernel-3.4.x.config"
fi

# Shrink /etc tmpfs hint for small Storage (optional, ignore if missing)
if [ -f "$ROOT/trunk/user/scripts/dev_init.sh" ]; then
  sed -i 's/size_etc="6M"/size_etc="2M"/g; s/size_etc="4M"/size_etc="2M"/g' \
    "$ROOT/trunk/user/scripts/dev_init.sh" || true
fi

# Dropbear: skip autoreconf (Ubuntu 22+ injects -fPIE/-D_FORTIFY that breaks
# cross zlib/crypt probes) and point zlib at the staged cross lib.
DB_MK="$ROOT/trunk/user/dropbear/Makefile"
if [ -f "$DB_MK" ]; then
  sed -i 's/[[:space:]]*autoreconf -v;[[:space:]]*//' "$DB_MK"
  if ! grep -q -- '--with-zlib=' "$DB_MK"; then
    sed -i 's|--enable-zlib|--enable-zlib --with-zlib=$(STAGEDIR)|' "$DB_MK"
  fi
  echo "[prepare] patched dropbear Makefile for cross zlib"
fi

# Enforce 64MB RAM / no media (avoid silentoldconfig NEW prompts)
KCFG="$BOARD_DST/kernel-3.4.x.config"
sed -i 's/^CONFIG_RALINK_RAM_SIZE=.*/CONFIG_RALINK_RAM_SIZE=64/' "$KCFG"
sed -i 's/^CONFIG_MEDIA_SUPPORT=.*/# CONFIG_MEDIA_SUPPORT is not set/' "$KCFG"
grep -q 'CONFIG_USB_VIDEO_CLASS_INPUT_EVDEV' "$KCFG" || \
  echo '# CONFIG_USB_VIDEO_CLASS_INPUT_EVDEV is not set' >> "$KCFG"

echo "[prepare] board files:"
ls -la "$BOARD_DST"
grep -E 'STORE_PART|RALINK_RAM_SIZE|FIRMWARE_ENABLE_USB|PRODUCT_ID|BTN_RESET|RT_SECOND' \
  "$BOARD_DST/kernel-3.4.x.config" \
  "$BOARD_DST/board.h" \
  "$TMPL_DST/HC5661A.config" | head -50 || true

echo "[prepare] done"
