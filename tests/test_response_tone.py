import wave

import pytest

from sounds.create_test_tone import create_test_tone


def test_create_local_tone_without_repository_binary(tmp_path):
    output = tmp_path / "response.wav"
    create_test_tone(output)

    with wave.open(str(output), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16_000
        assert wav.getnframes() == 16_000

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        create_test_tone(output)
