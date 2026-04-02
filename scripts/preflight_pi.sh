#!/bin/bash
# Preflight Check for ARM64 Raspberry Pi Runner
# Verifies USB storage and system readiness before deployment.

set -e

MOUNT_POINT="/mnt/usb-storage"
APP_USER="webapp"

echo "--- ARM64 Preflight Check Starting ---"

# 0. Architecture Check
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "ERROR: Expected aarch64 (ARM64) architecture, but found $ARCH"
    exit 1
fi
echo "✅ Architecture verified: $ARCH"

# 1. Verify USB Mount
if ! mountpoint -q "$MOUNT_POINT"; then
    echo "ERROR: USB storage is NOT mounted at $MOUNT_POINT"
    echo "Please check your /etc/fstab and physical connection."
    exit 1
fi
echo "✅ USB storage is mounted."

# 2. Verify Directory Structure & Write Permissions
REQUIRED_DIRS=(
    "$MOUNT_POINT/docker-volumes"
    "$MOUNT_POINT/backups"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Creating missing directory: $dir"
        sudo mkdir -p "$dir"
        sudo chown "$APP_USER":"$APP_USER" "$dir"
        sudo chmod 770 "$dir"
    fi
    # Write Test
    if ! sudo -u "$APP_USER" touch "$dir/.write_test"; then
        echo "ERROR: User $APP_USER cannot write to $dir"
        exit 1
    fi
    rm -f "$dir/.write_test"
    echo "✅ Directory exists and is writable: $dir"
done

# 3. Check Disk Space
FREE_SPACE=$(df -h "$MOUNT_POINT" | awk 'NR==2 {print $4}' | sed 's/G//')
if (( $(echo "$FREE_SPACE < 2.0" | bc -l) )); then
    echo "WARNING: Low disk space on USB storage ($FREE_SPACE GB remaining)."
else
    echo "✅ Sufficient disk space ($FREE_SPACE GB)."
fi

# 4. NTP Sync Check (Critical for TOTP/JWT)
if ! timedatectl status | grep -q "System clock synchronized: yes"; then
    echo "WARNING: System clock is NOT synchronized. JWT/TOTP tokens may fail."
else
    echo "✅ Clock is synchronized."
fi

# 5. Docker Permission Check
if ! groups "$APP_USER" | grep -q "\bdocker\b"; then
    echo "ERROR: User $APP_USER is not in the 'docker' group."
    exit 1
fi
echo "✅ Docker permissions verified."

# 6. Swap Space Check (Safety for 2GB RAM)
SWAP_TOTAL=$(free -m | grep "Swap:" | awk '{print $2}')
if [ "$SWAP_TOTAL" -eq 0 ]; then
    echo "WARNING: No swap space detected. 2GB RAM may be insufficient for MongoDB spikes."
else
    echo "✅ Swap space detected: ${SWAP_TOTAL}MB"
fi

echo "--- Preflight Complete: System is Ready ---"
