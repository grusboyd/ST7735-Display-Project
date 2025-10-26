#ifndef DISPLAY_SNAPSHOT_H
#define DISPLAY_SNAPSHOT_H

#include <Arduino.h>
#include <Adafruit_ST7735.h>
#include <stdint.h>

// Snapshot header stored at the start of the allocated block
struct SnapshotHeader {
  uint16_t width;   // captured width (pixels)
  uint16_t height;  // captured height (pixels)
  int16_t  offsetX; // x offset where the rectangle was drawn on the display
  int16_t  offsetY; // y offset where the rectangle was drawn on the display
};

// Lightweight API for capturing/restoring a rectangular snapshot of pixels.
// Implementation stores a single contiguous allocation: [SnapshotHeader][uint16_t pixels...]
// - captureFromBuffer() copies pixels from an existing in-memory buffer (recommended)
// - captureFromDisplay() is provided but may be unsupported depending on your driver
// - restoreToDisplay() draws pixels back to the provided Adafruit_ST7735 instance

namespace DisplaySnapshot {

// Returns true if a snapshot is currently stored in RAM
bool hasSnapshot();

// Capture pixels from an existing buffer (row-major uint16_t RGB565). This is the recommended
// and fast approach when you already have the pixel source (for example, captured during serial upload).
// src points to width*height uint16_t elements. The function makes an internal copy.
bool captureFromBuffer(const uint16_t *src, uint16_t width, uint16_t height, int16_t offsetX, int16_t offsetY);

// Attempt to capture pixels directly from the display. Many ST7735 drivers do not support reading
// pixels back; this function may fail and return false on those setups. If successful, a snapshot is stored.
bool captureFromDisplay(Adafruit_ST7735 &tft, uint16_t x, uint16_t y, uint16_t width, uint16_t height);

// Restore the stored snapshot to the provided display instance. Returns true on success.
bool restoreToDisplay(Adafruit_ST7735 &tft);

// Discard any stored snapshot and free memory.
void discardSnapshot();

// Return a pointer to the snapshot header (read-only) or nullptr if no snapshot present.
const SnapshotHeader *getSnapshotHeader();

} // namespace DisplaySnapshot

#endif // DISPLAY_SNAPSHOT_H
