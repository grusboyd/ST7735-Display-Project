#!/bin/bash
# sync-both.sh - Push current branch to both GitHub repositories
# Usage: ./sync-both.sh [branch-name]
# Default branch: master

BRANCH=${1:-master}

echo "Syncing branch '$BRANCH' to both repositories..."
echo ""

echo "→ Pushing to origin (grusboyd/ST7735-Display-Project)..."
if git push origin "$BRANCH" --tags; then
    echo "✓ Pushed to origin"
else
    echo "✗ Failed to push to origin"
    exit 1
fi

echo ""
echo "→ Pushing to origin-noetic (noeticrusty/ST7735_image_display)..."
if git push origin-noetic "$BRANCH" --tags; then
    echo "✓ Pushed to origin-noetic"
else
    echo "✗ Failed to push to origin-noetic"
    exit 1
fi

echo ""
echo "✓ Successfully synced to both GitHub repositories!"
