# Dogwatch

Dogwatch is a local little bark monitor for my MacBook. The idea is simple: listen for repeated dog barking, count those bark events, and play a prerecorded response when the barking crosses a threshold during quiet hours.

It is meant for home use, not as a professional sound meter or training system. The whole point is to keep it private and local: no accounts, no cloud audio processing, no uploading microphone audio anywhere.

## What It Does

Dogwatch watches for barking through the MacBook microphone. When it sees enough bark detections in a rolling time window, it plays a local response audio file through the MacBook speakers.

The current defaults are tuned around this flow:

- watch for bark-like sounds
- count repeated detections
- trigger after enough barks happen close together
- play the response file
- ignore its own playback
- wait through a cooldown
- go back to listening

A single bark should not trigger the response. The trigger is based on repeated barking.

## How Detection Works

The live detector now follows the same general approach as the working browser detector from dogbarkingdetector.com.

The dashboard runs a local browser-based YAMNet detector using TensorFlow.js. The model files are served from this project on `localhost`, so the model still runs on the laptop. The browser listens to the microphone, processes short audio windows locally, and looks for dog-related YAMNet classes such as `Dog`, `Bark`, `Bow-wow`, `Animal`, and `Domestic animals, pets`.

When the browser detector finds a dog sound, it sends a local message to the Python app. Python handles the rest:

- bark counting
- quiet-hours checks
- cooldown
- playback suppression
- response playback
- configuration

So the machine-learning part runs locally in the browser, and the automation logic runs locally in Python.

## Dashboard

The dashboard is available at:

```text
http://127.0.0.1:8765
```

From there you can:

- start and stop listening
- see the current monitor state
- see how many barks have been counted
- see whether quiet hours are active
- test the response audio
- change the configuration

The dashboard is intentionally simple and local. It is not deployed anywhere.

## Configuration

Most behavior is controlled by `config.json`.

The important knobs are:

- `required_barks`: how many detections are needed before triggering
- `rolling_window_s`: how close together those detections need to be
- `quiet_start` and `quiet_end`: when automatic playback is allowed
- `cooldown_s`: how long to wait after playback
- `response_path`: the local audio file to play
- `bark_on_threshold`: detection sensitivity
- `website_detection_debounce_s`: minimum spacing between browser-style detections

Quiet hours can cross midnight. For example, `22:30` to `07:00` means Dogwatch can trigger overnight but not during the day.

## Privacy

Normal monitoring keeps audio in memory. Dogwatch does not continuously save microphone audio to disk and does not upload audio anywhere.

The only normal audio file on disk is the response file you choose, such as:

```text
sounds/response.wav
```

Sample recording tools exist for local testing, but recording is explicit and manual.

## Current Shape

This is still an MVP. It is meant to be easy to tune after trying it with real barking in the actual room.

The detection stack is intentionally modular so it can change later. The browser YAMNet detector works now because it matched the website that successfully detected the phone-played dog barks. If that is not good enough with Boci in the room, the next step would be collecting a few local bark and non-bark samples and adding a small local classifier on top.
