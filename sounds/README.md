# Response audio

No response recording or other binary audio is stored in Git. In particular, this
repository does **not** pretend to contain anyone's voice.

Choose one of these local workflows:

1. Copy your own lawful, humane WAV or AIFF recording into this directory, then set
   `response_path` in `config.json` to that file.
2. For dashboard/playback testing only, generate a quiet one-second 440 Hz tone:

   ```bash
   python sounds/create_test_tone.py sounds/response.wav
   ```

The default configuration expects `sounds/response.wav`, so normal startup gives a
clear validation error until you supply or generate it. Audio extensions in this
directory are ignored by Git to prevent accidental commits of private recordings.
Preview any response at low volume before enabling Dogwatch; a generated tone is not
a behavioral recommendation.
