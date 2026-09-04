import numpy as np

from detection.acoustic_bark import acoustic_bark_score


def test_bark_like_burst_scores_above_default_test_threshold():
    rate=16000
    t=np.arange(rate)/rate
    audio=np.zeros(rate,dtype=np.float32)
    burst=(np.sin(2*np.pi*650*t[:4000])+0.45*np.sin(2*np.pi*1700*t[:4000])).astype(np.float32)
    envelope=np.exp(-np.linspace(0,5,4000)).astype(np.float32)
    audio[4000:8000]=0.45*burst*envelope
    assert acoustic_bark_score(audio,rate) >= .18


def test_quiet_audio_scores_zero():
    assert acoustic_bark_score(np.zeros(16000,dtype=np.float32),16000) == 0


def test_sustained_phone_like_bark_playback_scores_above_threshold():
    rate=16000
    t=np.arange(rate)/rate
    carrier=np.sin(2*np.pi*520*t)+.65*np.sin(2*np.pi*1250*t)+.35*np.sin(2*np.pi*2400*t)
    modulation=.55+.45*np.maximum(0,np.sin(2*np.pi*7*t))
    audio=(.12*carrier*modulation).astype(np.float32)
    assert acoustic_bark_score(audio,rate) >= .18
