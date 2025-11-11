#!/bin/bash
# Backup PlatformIO directory to 480GB volume
# Deletes previous backup before creating new one

BACKUP_DEST="/media/boyd/10137caf-c2da-49f0-942f-5f7beece46431/Documents/backups"
SOURCE_DIR="/home/boyd/Documents/PlatformIO"

echo "=== PlatformIO Backup Script ==="
echo "Source: $SOURCE_DIR"
echo "Destination: $BACKUP_DEST"
echo ""

# Delete old backup if it exists
if [ -d "$BACKUP_DEST/PlatformIO" ]; then
    echo "Removing old backup..."
    rm -rf "$BACKUP_DEST/PlatformIO"
    echo "✓ Old backup removed"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DEST"

# Perform backup
echo ""
echo "Creating new backup..."
rsync -av --progress "$SOURCE_DIR" "$BACKUP_DEST/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Backup completed successfully!"
else
    echo ""
    echo "✗ Backup failed!"
    exit 1
fi
