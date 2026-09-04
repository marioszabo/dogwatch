# Dogwatch

Dogwatch is a **local-only, experimental** macOS bark-event monitor. By default, its dashboard runs the same browser TensorFlow.js YAMNet detector used by dogbarkingdetector.com, then sends local detections to Python for bark counting, quiet-hours checks, cooldown, and response playback. It is not a sound-level meter, safety device, veterinary tool, or substitute for humane training. Never use audio that frightens or harms an animal.

## Requirements and exact installation

Designed for a Mac with Apple Silicon (M2 tested target), macOS 13+, Python 3.12, Xcode command-line tools, and PortAudio. Install PortAudio and create an isolated environment:

```bash
brew install portaudio
cd /path/to/dogwatch
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The default runtime serves a local copy of the TensorFlow.js YAMNet model and WASM backend from `web/model` and `web/libs`; microphone audio is processed in the browser at `127.0.0.1` and is not uploaded. The optional `inference_runtime: "python"` path keeps the earlier Python TensorFlow Hub implementation for WAV validation and experimentation, but the normal live detector uses the browser runtime because it matched the working dogbarkingdetector.com behavior in testing.

## macOS microphone permission

On first launch, allow access. If no prompt appears, open **System Settings → Privacy & Security → Microphone**, enable the terminal (or IDE/app that launches Dogwatch), completely quit that application, and launch it again. Use `python -c "import sounddevice as s; print(s.query_devices())"` to inspect devices. The selected input device is logged at startup.

## Response file

No binary response audio is committed. Supply your own lawful, humane WAV/AIFF recording, or generate a quiet local test tone with `python sounds/create_test_tone.py sounds/response.wav`. The generated tone is not a spouse's voice, another person's recording, or a behavioral recommendation. The default `response_path` expects that local file and startup clearly fails until it exists. Audio files under `sounds/` are Git-ignored to avoid accidentally committing private recordings. Preview responses at low system volume; `afplay` performs local playback. Dogwatch suppresses real and simulated inputs for all of playback, post-playback suppression, and cooldown.

## Launch and dashboard

```bash
source .venv/bin/activate
python app.py                 # normal structured JSON logs
python app.py --debug         # verbose structured JSON logs
```

Open <http://127.0.0.1:8765>. It is intentionally bound only to loopback. Click **Start Browser Detector** and allow microphone access in the browser if prompted. The dashboard reports state, event count, YAMNet confidence, and the dog-related class scores used by the detector. **Simulate Bark** and **Simulate 5 Barks** use the same local state-machine route as real detections. **Test Response** uses actual playback and the complete suppression lifecycle. Ctrl-C/SIGTERM gracefully stops HTTP and microphone capture.

## Configuration

`config.json` defaults to enabled, 22:30–07:00 quiet hours (end exclusive), five events in 30 seconds, and:

| Key | Meaning |
|---|---|
| `enabled` | Master detection switch |
| `inference_runtime` | `browser` for the local TFJS detector, `python` for the older Python TensorFlow path |
| `quiet_start`, `quiet_end` | Local `HH:MM`; supports midnight crossing; equal means all day |
| `bark_on_threshold`, `bark_off_threshold` | Detection sensitivity; off must be lower for the Python event segmenter |
| `min_event_duration_s` | Discard shorter high-confidence spikes |
| `release_duration_s` | Low confidence must persist this long before finalization |
| `min_event_gap_s` | Minimum separation after a finalized event |
| `rolling_window_s`, `required_barks` | Finalized-event trigger window and count |
| `post_playback_suppression_s`, `cooldown_s` | Continued input rejection after playback |
| `response_path` | Local response audio |
| `rms_gate_dbfs` | Optional digital energy gate; `null` disables it |
| `dog_specific_floor` | Minimum score for a specific dog class before generic animal scores can count |
| `website_detection_debounce_s` | Minimum seconds between browser-style YAMNet detections |

Unknown keys, wrong types, non-finite/out-of-range values, invalid times, unsafe relative paths, and malformed JSON are rejected with explicit messages. Applying configuration clears stale event-count and segmentation state.

## Calibration and threshold tuning

Put the computer at the intended location, approximately **1 meter from the dog** (an environmental assumption, not a calibrated acoustic measurement), then run:

```bash
python app.py --calibrate
```

Observe background and representative bark values. These are **dBFS (digital full scale), not calibrated dB SPL**. Set `rms_gate_dbfs` above steady electronic/background noise but below quiet barks. Then use a labeled WAV and tune `bark_on_threshold` against YAMNet confidence; keep `bark_off_threshold` lower. Test across distances, rooms, speech, television, and other dogs. False positives/negatives are expected.

Segmentation begins at the on-threshold, treats intervening uncertain frames as continuity, and finalizes only after the off-threshold persists for `release_duration_s`. A high period shorter than `min_event_duration_s` is discarded. `min_event_gap_s` prevents one physical burst from splitting; truly separated bursts yield distinct events. Counting uses finalized events—not inference frames.

## WAV validation and inference performance

```bash
python test_yamnet.py /absolute/path/to/known-bark.wav
```

The utility validates WAV decoding, converts integer/stereo audio to mono float32, sanitizes non-finite values, resamples to 16 kHz, prints top classes at a rate-limited interval, bark confidence, and average/p95 inference latency. Use a known, licensed WAV; corrupt/unsupported input gets a clear nonzero error. Do not infer real-time fitness from one file alone.

## Recording samples

No recordings are bundled. Marker-only directories are provided at `samples/bark`, `samples/non_bark`, and `samples/other`. Record only where consent and local law allow, to an explicit new path, for at most 60 seconds:

```bash
python record_sample.py samples/bark/my-bark.wav --duration 5
```

The tool refuses overwrite and keeps capture bounded. Review recordings before sharing or committing them.

## Tests

```bash
python -m pytest -q
```

Tests cover defaults and invalid updates, generated-signal conversion/resampling/gating, schedule boundaries, every state, suppression, window pruning, and frame-to-event behavior (continuous highs, discarded spikes, persistent release, separated bursts). Unit tests mock the heavyweight classifier/player; `test_yamnet.py` is the real-model integration check.

## Resource monitoring

During representative operation use Activity Monitor (CPU, Memory, Energy), `powermetrics` where authorized, or:

```bash
ps -o pid,%cpu,%mem,rss,etime -p "$(pgrep -n -f 'python app.py')"
```

Record warm-model average/p95 latency from `test_yamnet.py`, dropped capture blocks from logs, temperature, sample duration, and Mac model. Long inference stalls can overflow the deliberately bounded queue; old audio is dropped rather than allowing unbounded memory growth.

## Troubleshooting

* **Model download fails:** confirm network access, free cache space, and `TFHUB_CACHE_DIR`; retry once online. Preserve the cache for offline use.
* **No microphone / permission error:** follow the permission steps above, inspect `sounddevice` devices, and verify no exclusive audio application is holding input.
* **`PortAudioError`:** `brew reinstall portaudio`, reactivate the environment, then reinstall `sounddevice`.
* **Response fails:** ensure the path exists, is nonempty/readable, and `/usr/bin/afplay file.wav` succeeds. Start at low volume.
* **No triggers:** confirm current local time is inside quiet hours, state is LISTENING/COUNTING, RMS gate is not too high, and inspect confidence in debug/WAV output.
* **Too many triggers:** increase onset/minimum duration/gap or required count, shorten the window, and add representative non-bark validation files.

## Privacy and validation record

Raw microphone samples remain in bounded RAM queues and are never written by the service. Only `record_sample.py`, when explicitly invoked with a path, writes audio. The dashboard is loopback-only; nevertheless, treat configuration and logs as sensitive.

Repository CI/container tests do **not** establish microphone permission, acoustic performance, behavior with a real dog, M2 latency, or safe volume. On the actual M2 deployment, separately record: dependency installation/macOS version; unit result; known-WAV source/result; dashboard five-event and safe playback result; warm average/p95 latency; microphone device/permission check; and any real-dog check actually and ethically performed. Never claim an unperformed physical check.
