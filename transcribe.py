"""Transcribe audio files locally using Whisper.

Usage:
    uv run python transcribe.py input/reel.mp3 --language pt --model base --print
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

SUPPORTED_EXTENSIONS = (".mp3",)
SUPPORTED_MODELS = ("tiny", "base", "small", "medium", "large")

DEFAULT_MODEL = os.getenv("WHISPER_MODEL", "base")
DEFAULT_OUTPUT_DIR = os.getenv("WHISPER_OUTPUT_DIR", "output")

EXIT_SUCCESS = 0
EXIT_FILE_NOT_FOUND = 3
EXIT_UNSUPPORTED_FORMAT = 4
EXIT_EMPTY_FILE = 5
EXIT_INVALID_MODEL = 6
EXIT_TRANSCRIPTION_FAILED = 7
EXIT_WRITE_FAILED = 8


class TranscriptionError(Exception):
    """Error with a message meant for the user and a shell exit code."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class Transcription:
    """Result of a transcription run."""

    text: str
    language: Optional[str] = None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        prog="transcribe.py",
        description="Transcribe an audio file locally using Whisper.",
    )
    parser.add_argument("file", help="path to the audio file to transcribe")
    parser.add_argument(
        "--language",
        default=None,
        help="language of the audio (e.g. pt). Detected automatically when omitted",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Whisper model to use. One of: {', '.join(SUPPORTED_MODELS)} (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"directory where the transcription is saved (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--print",
        dest="print_transcript",
        action="store_true",
        help="print the transcription to the terminal",
    )
    return parser.parse_args(argv)


def validate_audio_file(file_path: str | Path) -> Path:
    """Return the audio file path, raising when it cannot be transcribed."""
    path = Path(file_path)

    if not path.is_file():
        raise TranscriptionError(
            f"Audio file not found: {path}", EXIT_FILE_NOT_FOUND
        )

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        raise TranscriptionError(
            f"Unsupported file format: {path.suffix or '(none)'}. Supported formats: {supported}",
            EXIT_UNSUPPORTED_FORMAT,
        )

    if path.stat().st_size == 0:
        raise TranscriptionError(f"Audio file is empty: {path}", EXIT_EMPTY_FILE)

    return path


def validate_model(model_name: str) -> str:
    """Return the model name, raising when it is not supported."""
    if model_name not in SUPPORTED_MODELS:
        supported = ", ".join(SUPPORTED_MODELS)
        raise TranscriptionError(
            f"Invalid model: {model_name}. Supported models: {supported}",
            EXIT_INVALID_MODEL,
        )
    return model_name


def build_output_path(audio_path: str | Path, output_dir: str | Path) -> Path:
    """Map an audio file to its transcription file inside the output directory."""
    return Path(output_dir) / f"{Path(audio_path).stem}.txt"


def load_whisper_model(model_name: str):
    """Load a Whisper model. Imported lazily to keep CLI startup fast."""
    import whisper

    return whisper.load_model(model_name)


def transcribe_audio(
    audio_path: str | Path,
    model_name: str,
    language: Optional[str] = None,
    model_loader: Optional[Callable[[str], object]] = None,
) -> Transcription:
    """Transcribe the audio file, loading the Whisper model once."""
    loader = model_loader or load_whisper_model
    try:
        model = loader(model_name)
        result = model.transcribe(str(audio_path), language=language)
    except Exception as error:  # noqa: BLE001 - surfaced to the user as a clear message
        raise TranscriptionError(
            f"Transcription failed: {error}", EXIT_TRANSCRIPTION_FAILED
        ) from error

    return Transcription(
        text=str(result.get("text", "")).strip(),
        language=result.get("language") or language,
    )


def write_transcript(text: str, output_path: str | Path) -> Path:
    """Write the transcription, creating the output directory when needed."""
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{text}\n", encoding="utf-8")
    except OSError as error:
        raise TranscriptionError(
            f"Could not save the transcription to {path}: {error}", EXIT_WRITE_FAILED
        ) from error
    return path


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return the process exit code."""
    args = parse_args(argv)

    try:
        audio_path = validate_audio_file(args.file)
        model_name = validate_model(args.model)
        output_path = build_output_path(audio_path, args.output)
        transcription = transcribe_audio(audio_path, model_name, args.language)
        write_transcript(transcription.text, output_path)
    except TranscriptionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return error.exit_code

    print("Transcription completed successfully.")
    print(f"Input: {audio_path}")
    print(f"Output: {output_path}")
    print(f"Language: {transcription.language or 'auto'}")
    print(f"Model: {model_name}")

    if args.print_transcript:
        print()
        print(transcription.text)

    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
