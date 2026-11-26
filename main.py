#!/usr/bin/env python3
"""Validate and export the bundled infographic without third-party modules."""

import os
from pathlib import Path
import struct
import sys


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024


def validate_png(data):
    """Check the PNG signature and the first IHDR chunk before copying."""
    byte_count = len(data)
    if byte_count > MAX_BYTES:
        raise ValueError(f"PNG exceeds {MAX_BYTES} bytes: {byte_count}")
    # A complete IHDR includes its length, type, 13-byte payload, and CRC.
    if byte_count < 33:
        raise ValueError("File is too short to contain a PNG IHDR")
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Invalid PNG magic bytes")
    if data[8:12] != struct.pack(">I", 13) or data[12:16] != b"IHDR":
        raise ValueError("PNG must begin with a 13-byte IHDR chunk")
    # PNG stores both dimensions as unsigned big-endian integers at 16:24.
    width, height = struct.unpack(">II", data[16:24])
    if not (1 <= width <= MAX_DIMENSION):
        raise ValueError(f"Width outside 1..{MAX_DIMENSION}: {width}")
    if not (1 <= height <= MAX_DIMENSION):
        raise ValueError(f"Height outside 1..{MAX_DIMENSION}: {height}")
    return width, height


def main():
    """Read the adjacent asset and write its exact bytes to the output dir."""
    source = Path(__file__).resolve().parent / "entry.png"
    try:
        # Validate the bytes that will actually be written, without decoding.
        data = source.read_bytes()
        width, height = validate_png(data)
        output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "entry.png"
        written = destination.write_bytes(data)
        if written != len(data):
            raise OSError("Output byte count differs from input")
        # A read-back catches unexpected changes in the output file.
        if destination.read_bytes() != data:
            raise OSError("Output bytes differ from the validated PNG")
        print(f"Copied {written} bytes ({width}x{height}) to {destination}")
        return 0
    except (OSError, ValueError, struct.error) as error:
        print(f"entry.png validation/export failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
