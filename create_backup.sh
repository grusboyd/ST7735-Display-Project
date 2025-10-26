#!/bin/bash
# Create timestamped backup of main.cpp before making changes
# Usage: ./create_backup.sh [optional_description]

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DESCRIPTION=""

if [ "$1" != "" ]; then
    DESCRIPTION="_$1"
fi

BACKUP_FILE="backups/main.cpp.backup_${TIMESTAMP}${DESCRIPTION}"

mkdir -p backups
cp src/main.cpp "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
ls -la "$BACKUP_FILE"