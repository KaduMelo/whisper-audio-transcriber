"""Unit tests for the transcribe CLI. Whisper is always mocked."""

from __future__ import annotations

from pathlib import Path

import pytest

import transcribe
from transcribe import (
    EXIT_EMPTY_FILE,
    EXIT_FILE_NOT_FOUND,
    EXIT_INVALID_MODEL,
    EXIT_SUCCESS,
    EXIT_TRANSCRIPTION_FAILED,
    EXIT_UNSUPPORTED_FORMAT,
    TranscriptionError,
    build_output_path,
    main,
    parse_args,
    transcribe_audio,
    validate_audio_file,
    validate_model,
    write_transcript,
)


class FakeWhisperModel:
    """Stand-in for a loaded Whisper model."""

    def __init__(self, text: str = "hello world", language: str = "pt") -> None:
        self.text = text
        self.language = language
        self.calls: list[tuple[str, str | None]] = []

    def transcribe(self, audio_path: str, language: str | None = None) -> dict:
        self.calls.append((audio_path, language))
        return {"text": f" {self.text} ", "language": language or self.language}


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    path = tmp_path / "reel.mp3"
    path.write_bytes(b"fake audio")
    return path


# --- argument parsing -------------------------------------------------------


def test_parse_args_uses_defaults():
    args = parse_args(["audio.mp3"])

    assert args.file == "audio.mp3"
    assert args.language is None
    assert args.model == transcribe.DEFAULT_MODEL
    assert args.output == transcribe.DEFAULT_OUTPUT_DIR
    assert args.print_transcript is False


def test_parse_args_reads_all_options():
    args = parse_args(
        ["reel.mp3", "--language", "pt", "--model", "small", "--output", "./transcripts", "--print"]
    )

    assert args.file == "reel.mp3"
    assert args.language == "pt"
    assert args.model == "small"
    assert args.output == "./transcripts"
    assert args.print_transcript is True


def test_parse_args_requires_a_file():
    with pytest.raises(SystemExit):
        parse_args([])


# --- file validation --------------------------------------------------------


def test_validate_audio_file_returns_path(audio_file: Path):
    assert validate_audio_file(audio_file) == audio_file


def test_validate_audio_file_rejects_missing_file(tmp_path: Path):
    with pytest.raises(TranscriptionError) as excinfo:
        validate_audio_file(tmp_path / "missing.mp3")

    assert excinfo.value.exit_code == EXIT_FILE_NOT_FOUND
    assert "not found" in str(excinfo.value)


def test_validate_audio_file_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"fake audio")

    with pytest.raises(TranscriptionError) as excinfo:
        validate_audio_file(path)

    assert excinfo.value.exit_code == EXIT_UNSUPPORTED_FORMAT


def test_validate_audio_file_rejects_empty_file(tmp_path: Path):
    path = tmp_path / "empty.mp3"
    path.touch()

    with pytest.raises(TranscriptionError) as excinfo:
        validate_audio_file(path)

    assert excinfo.value.exit_code == EXIT_EMPTY_FILE


def test_validate_audio_file_rejects_directory(tmp_path: Path):
    with pytest.raises(TranscriptionError) as excinfo:
        validate_audio_file(tmp_path)

    assert excinfo.value.exit_code == EXIT_FILE_NOT_FOUND


# --- model validation -------------------------------------------------------


@pytest.mark.parametrize("model_name", transcribe.SUPPORTED_MODELS)
def test_validate_model_accepts_supported_models(model_name: str):
    assert validate_model(model_name) == model_name


def test_validate_model_rejects_unknown_model():
    with pytest.raises(TranscriptionError) as excinfo:
        validate_model("gigantic")

    assert excinfo.value.exit_code == EXIT_INVALID_MODEL


# --- output path ------------------------------------------------------------


def test_build_output_path_replaces_extension_and_directory():
    assert build_output_path("input/reel.mp3", "output") == Path("output/reel.txt")


def test_build_output_path_honours_custom_directory():
    assert build_output_path("/audios/ReelAudio-82149.mp3", "./transcripts") == Path(
        "transcripts/ReelAudio-82149.txt"
    )


# --- transcription service --------------------------------------------------


def test_transcribe_audio_loads_model_once_and_returns_text(audio_file: Path):
    model = FakeWhisperModel(text="olá mundo")
    loads: list[str] = []

    def loader(model_name: str) -> FakeWhisperModel:
        loads.append(model_name)
        return model

    result = transcribe_audio(audio_file, "base", language="pt", model_loader=loader)

    assert loads == ["base"]
    assert result.text == "olá mundo"
    assert result.language == "pt"
    assert model.calls == [(str(audio_file), "pt")]


def test_transcribe_audio_keeps_detected_language(audio_file: Path):
    model = FakeWhisperModel(language="en")

    result = transcribe_audio(audio_file, "base", model_loader=lambda _: model)

    assert result.language == "en"
    assert model.calls == [(str(audio_file), None)]


def test_transcribe_audio_wraps_failures(audio_file: Path):
    def failing_loader(_: str):
        raise RuntimeError("model download failed")

    with pytest.raises(TranscriptionError) as excinfo:
        transcribe_audio(audio_file, "base", model_loader=failing_loader)

    assert excinfo.value.exit_code == EXIT_TRANSCRIPTION_FAILED
    assert "model download failed" in str(excinfo.value)


# --- writing the transcript -------------------------------------------------


def test_write_transcript_creates_missing_directories(tmp_path: Path):
    output_path = tmp_path / "output" / "reel.txt"

    write_transcript("olá mundo", output_path)

    assert output_path.read_text(encoding="utf-8") == "olá mundo\n"


def test_write_transcript_reports_write_errors(tmp_path: Path):
    blocker = tmp_path / "output"
    blocker.write_text("not a directory", encoding="utf-8")

    with pytest.raises(TranscriptionError):
        write_transcript("olá mundo", blocker / "reel.txt")


# --- CLI end to end (Whisper mocked) ----------------------------------------


def test_main_writes_transcription_and_reports(audio_file, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(transcribe, "load_whisper_model", lambda _: FakeWhisperModel("olá mundo"))
    output_dir = tmp_path / "output"

    exit_code = main([str(audio_file), "--language", "pt", "--output", str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert (output_dir / "reel.txt").read_text(encoding="utf-8") == "olá mundo\n"
    assert "Transcription completed successfully." in captured.out
    assert f"Input: {audio_file}" in captured.out
    assert f"Output: {output_dir / 'reel.txt'}" in captured.out
    assert "Language: pt" in captured.out
    assert "Model: base" in captured.out
    assert "olá mundo" not in captured.out.split("Model: base")[1]


def test_main_prints_transcription_with_print_flag(audio_file, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(transcribe, "load_whisper_model", lambda _: FakeWhisperModel("olá mundo"))

    exit_code = main(
        [str(audio_file), "--model", "small", "--output", str(tmp_path / "out"), "--print"]
    )

    captured = capsys.readouterr()
    assert exit_code == EXIT_SUCCESS
    assert "Model: small" in captured.out
    assert captured.out.strip().endswith("olá mundo")


def test_main_returns_error_code_for_missing_file(tmp_path, capsys):
    exit_code = main([str(tmp_path / "missing.mp3")])

    captured = capsys.readouterr()
    assert exit_code == EXIT_FILE_NOT_FOUND
    assert captured.err.startswith("Error: Audio file not found:")


def test_main_returns_error_code_for_invalid_model(audio_file, capsys):
    exit_code = main([str(audio_file), "--model", "gigantic"])

    captured = capsys.readouterr()
    assert exit_code == EXIT_INVALID_MODEL
    assert "Invalid model: gigantic" in captured.err
