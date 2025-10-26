#include "display_snapshot.h"
#include <stdlib.h>
#include <string.h>

// Single contiguous allocation containing SnapshotHeader followed by width*height uint16_t pixels
static uint8_t *g_snapshot = nullptr;
static size_t  g_snapshot_size = 0;

namespace DisplaySnapshot {

bool hasSnapshot() {
  return g_snapshot != nullptr;
}

const SnapshotHeader *getSnapshotHeader() {
  if (!g_snapshot) return nullptr;
  return (const SnapshotHeader *)g_snapshot;
}

bool captureFromBuffer(const uint16_t *src, uint16_t width, uint16_t height, int16_t offsetX, int16_t offsetY) {
  if (!src || width == 0 || height == 0) return false;

  // Calculate required bytes and sanity-check size
  size_t pixels = (size_t)width * (size_t)height;
  size_t bytes_needed = sizeof(SnapshotHeader) + pixels * sizeof(uint16_t);
  // Avoid oversized allocations on the Due (simple safety limit ~60KB)
  if (bytes_needed > 60UL * 1024UL) return false;

  // Allocate new block
  uint8_t *buf = (uint8_t*)malloc(bytes_needed);
  if (!buf) return false;

  // Fill header
  SnapshotHeader *hdr = (SnapshotHeader*)buf;
  hdr->width = width;
  hdr->height = height;
  hdr->offsetX = offsetX;
  hdr->offsetY = offsetY;

  // Copy pixel data (uint16_t RGB565, row-major)
  uint16_t *pixelsPtr = (uint16_t*)(buf + sizeof(SnapshotHeader));
  memcpy(pixelsPtr, src, pixels * sizeof(uint16_t));

  // Free previous snapshot if any
  if (g_snapshot) {
    free(g_snapshot);
  }

  g_snapshot = buf;
  g_snapshot_size = bytes_needed;
  return true;
}

bool captureFromDisplay(Adafruit_ST7735 &tft, uint16_t x, uint16_t y, uint16_t width, uint16_t height) {
  // Many ST7735 drivers (including common Adafruit_ST7735) don't implement a readPixel API.
  // Implementing a generic read-back is driver-dependent and can be slow. This function attempts
  // to provide a hook but will return false to indicate unsupported on this platform.
  (void)tft; (void)x; (void)y; (void)width; (void)height;
  return false; // Not supported in this reference implementation.
}

bool restoreToDisplay(Adafruit_ST7735 &tft) {
  if (!g_snapshot) return false;
  SnapshotHeader *hdr = (SnapshotHeader*)g_snapshot;
  uint16_t *pixelsPtr = (uint16_t*)(g_snapshot + sizeof(SnapshotHeader));

  // Draw pixels back to the display. This is intentionally simple and uses tft.drawPixel;
  // it's correct but may not be the fastest approach for large blocks.
  for (uint16_t r = 0; r < hdr->height; ++r) {
    for (uint16_t c = 0; c < hdr->width; ++c) {
      int dx = hdr->offsetX + (int)c;
      int dy = hdr->offsetY + (int)r;
      // Basic bounds check against the display; use tft.width()/height()
      if (dx >= 0 && dx < (int)tft.width() && dy >= 0 && dy < (int)tft.height()) {
        uint16_t px = pixelsPtr[r * hdr->width + c];
        tft.drawPixel(dx, dy, px);
      }
    }
  }
  return true;
}

void discardSnapshot() {
  if (g_snapshot) {
    free(g_snapshot);
    g_snapshot = nullptr;
    g_snapshot_size = 0;
  }
}

} // namespace DisplaySnapshot
