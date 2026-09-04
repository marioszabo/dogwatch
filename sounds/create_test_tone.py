#!/usr/bin/env python3
"""Create a local WAV test tone without storing binary audio in Git."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import struct
import wave


def create_test_tone(output: Path, *, duration_s: float = 1.0) -> None:
    """Write a quiet 440 Hz mono PCM WAV, refusing to overwrite files."""
    if output.suffix.lower() != ".wav":
        raise ValueError("output path must end in .wav")
    if not 0.1 <= duration_s <= 10.0:
        raise ValueError("duration must be between 0.1 and 10 seconds")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16_000
    frame_count = round(duration_s * sample_rate)
    with output.open("xb") as raw, wave.open(raw, "wb") as wav:
        wav.setparams((1, 2, sample_rate, frame_count, "NONE", "test tone"))
        frames = bytearray()
        for index in range(frame_count):
            sample = int(0.1 * 32_767 * math.sin(2 * math.pi * 440 * index / sample_rate))
            frames.extend(struct.pack("<h", sample))
        wav.writeframes(frames)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a quiet local test tone (not a human recording)."
    )
    parser.add_argument("output", type=Path, help="new .wav path to create")
    parser.add_argument("--duration", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        create_test_tone(args.output, duration_s=args.duration)
    except (ValueError, FileExistsError, OSError, wave.Error) as exc:
        parser.error(str(exc))
    print(f"created local test tone: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
