#!/bin/bash
# Preflight Check for ARM64 Raspberry Pi Runner
set -e

APP_USER="webapp"

echo "--- ARM64 Hardware Verification ---"

# 1. Architecture Check
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "ERROR: Expected aarch64 (ARM64) architecture, but found $ARCH"
    exit 1
fi
echo "✅ Architecture verified: $ARCH"

# 2. Docker Permission Check
if ! groups "$APP_USER" | grep -q "\bdocker\b"; then
    echo "ERROR: User $APP_USER is not in the 'docker' group."
    exit 1
fi
echo "✅ Docker permissions verified."

# 3. Storage Warning (Non-blocking)
MOUNT_POINT="/mnt/usb-storage"
if ! mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
    echo "⚠️  Note: USB storage not mounted at $MOUNT_POINT. Audit will use local storage."
fi

echo "--- Preflight Complete: Proceeding with Disposable Audit ---"
