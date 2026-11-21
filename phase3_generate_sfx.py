#!/usr/bin/env python3
"""
Phase 3: Synthesize Broadcast-Quality Cinema SFX & Ambient Background Bed
Outputs in sfx_library/:
  1. whoosh.wav          (0.35s) - Filtered pink-noise sweep 200Hz -> 2200Hz
  2. bass_hit.wav        (0.80s) - Deep sub-bass cinematic boom 85Hz -> 35Hz
  3. riser.wav           (1.50s) - Ascending harmonic tension swell
  4. heartbeat.wav       (1.20s) - Low-pass double thump (55Hz)
  5. bg_ambient_bed.mp3  (485.0s) - Dark, subtle cinematic ambient pad at -29 dB
"""

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parent
SFX_DIR = ROOT / "sfx_library"
SR = 48000


def find_ffmpeg() -> str:
    for cand in [shutil.which("ffmpeg"), "/tmp/venv/bin/ffmpeg"]:
        if cand and os.path.exists(cand):
            return cand
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def save_stereo_wav(path: Path, stereo: np.ndarray, peak_db: float = -1.5) -> None:
    """Normalize stereo float array (-1..1) to target peak_db and save 16-bit PCM WAV."""
    max_abs = float(np.max(np.abs(stereo))) + 1e-12
    target_amp = 10.0 ** (peak_db / 20.0)
    scaled = np.clip(stereo / max_abs * target_amp, -1.0, 1.0)
    pcm = (scaled * 32767.0).astype(np.int16)
    wavfile.write(str(path), SR, pcm)


def pink_noise(n_samples: int, rng: np.random.Generator) -> np.ndarray:
    """Generate spectral 1/f pink noise."""
    white = rng.standard_normal(n_samples)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n_samples, 1.0 / SR)
    scale = 1.0 / np.sqrt(np.maximum(freqs, 20.0))
    scale[0] = 0.0
    pink = np.fft.irfft(fft * scale, n=n_samples)
    pink /= np.max(np.abs(pink)) + 1e-12
    return pink


def generate_whoosh(rng: np.random.Generator) -> np.ndarray:
    """0.35s filtered pink-noise frequency sweep (200Hz -> 2200Hz) with stereo movement."""
    dur = 0.35
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)

    # Time-varying bandpass sweep via overlap-add short windows
    src_l = pink_noise(n, rng)
    src_r = pink_noise(n, rng)

    out_l = np.zeros(n, dtype=np.float64)
    out_r = np.zeros(n, dtype=np.float64)
    win_len = 1024
    hop = 256
    window = np.hanning(win_len)
    norm = np.zeros(n, dtype=np.float64)

    for start in range(0, n, hop):
        end = min(start + win_len, n)
        seg_len = end - start
        if seg_len < 64:
            break
        progress = (start + seg_len * 0.5) / n
        # Exponential frequency sweep 200Hz -> 2200Hz
        center_hz = 200.0 * ((2200.0 / 200.0) ** progress)
        lo = max(60.0, center_hz * 0.55)
        hi = min(SR * 0.45, center_hz * 1.65)
        sos = butter(3, [lo, hi], btype="bandpass", fs=SR, output="sos")

        w = window[:seg_len]
        out_l[start:end] += sosfilt(sos, src_l[start:end]) * w
        out_r[start:end] += sosfilt(sos, src_r[start:end]) * w
        norm[start:end] += w

    norm = np.maximum(norm, 1e-6)
    out_l /= norm
    out_r /= norm

    # Smooth whoosh amplitude envelope peaking around 60%
    env = np.sin(np.pi * (t / dur) ** 0.78) ** 1.6
    # Subtle L->R stereo sweep
    pan = 0.5 + 0.25 * np.sin(np.pi * (t / dur - 0.5))
    left = out_l * env * np.sqrt(1.0 - pan)
    right = out_r * env * np.sqrt(pan)

    # Subtle sub-air body underneath
    sub_phase = 2.0 * np.pi * np.cumsum(np.linspace(90.0, 240.0, n)) / SR
    sub = 0.25 * np.sin(sub_phase) * env
    return np.column_stack([left + sub, right + sub])


def generate_bass_hit(rng: np.random.Generator) -> np.ndarray:
    """0.8s deep sub-bass cinematic boom (85Hz -> 35Hz)."""
    dur = 0.80
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)

    # Exponential pitch glide 85Hz -> 35Hz
    freq = 35.0 + (85.0 - 35.0) * np.exp(-t * 6.5)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR

    # Fundamental + subtle 2nd harmonic warmth + punch transient
    sub = np.sin(phase)
    warm = 0.28 * np.sin(2.0 * phase)
    punch_freq = 45.0 + 135.0 * np.exp(-t * 45.0)
    punch = 0.45 * np.sin(2.0 * np.pi * np.cumsum(punch_freq) / SR) * np.exp(-t * 28.0)

    # Low-passed noise impact crack
    impact_noise = sosfilt(butter(3, 420.0, btype="lowpass", fs=SR, output="sos"), rng.standard_normal(n))
    impact_noise = impact_noise / (np.max(np.abs(impact_noise)) + 1e-12) * 0.22 * np.exp(-t * 18.0)

    # Fast 4ms attack, long cinematic exponential tail
    attack = np.minimum(t / 0.004, 1.0)
    decay = np.exp(-t * 3.4) * (1.0 - np.maximum((t - 0.72) / 0.08, 0.0))
    body = np.tanh(1.35 * (sub + warm + punch)) * attack * decay

    left = body + impact_noise
    right = body + np.roll(impact_noise, 12)
    return np.column_stack([left, right])


def generate_riser(rng: np.random.Generator) -> np.ndarray:
    """1.5s ascending harmonic tension swell."""
    dur = 1.50
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)
    p = t / dur

    # Ascending fundamental (110Hz -> 392Hz) + detuned fifth + octave
    f1 = 110.0 * ((392.0 / 110.0) ** (p ** 1.35))
    f2 = f1 * 1.498  # Perfect fifth
    f3 = f1 * 2.006  # Slightly detuned octave for lush width
    f4 = f1 * 1.994

    ph1 = 2.0 * np.pi * np.cumsum(f1) / SR
    ph2 = 2.0 * np.pi * np.cumsum(f2) / SR
    ph3 = 2.0 * np.pi * np.cumsum(f3) / SR
    ph4 = 2.0 * np.pi * np.cumsum(f4) / SR

    tone_l = 0.45 * np.sin(ph1) + 0.25 * np.sin(ph2) + 0.22 * np.sin(ph3)
    tone_r = 0.45 * np.sin(ph1) + 0.25 * np.sin(ph2) + 0.22 * np.sin(ph4)

    # Rising filtered noise air
    noise = pink_noise(n, rng)
    shimmer = sosfilt(butter(2, [450.0, 5200.0], btype="bandpass", fs=SR, output="sos"), noise)
    shimmer /= np.max(np.abs(shimmer)) + 1e-12

    # Exponential tension swell with crisp cut at end
    swell = (p ** 2.2) * np.minimum((dur - t) / 0.035, 1.0)
    left = (tone_l + 0.35 * shimmer) * swell
    right = (tone_r + 0.35 * np.roll(shimmer, 24)) * swell
    return np.column_stack([left, right])


def generate_heartbeat() -> np.ndarray:
    """1.2s low-pass double thump (55Hz) for emotional tension."""
    dur = 1.20
    n = int(SR * dur)
    t = np.linspace(0.0, dur, n, endpoint=False)

    def thump(center_s: float, f_start: float, f_end: float, amp: float, width_s: float) -> np.ndarray:
        dt = t - center_s
        mask = dt >= 0.0
        sig = np.zeros(n, dtype=np.float64)
        dtm = dt[mask]
        freq = f_end + (f_start - f_end) * np.exp(-dtm * 18.0)
        ph = 2.0 * np.pi * np.cumsum(freq) / SR
        env = np.minimum(dtm / 0.008, 1.0) * np.exp(-dtm / width_s)
        sig[mask] = amp * np.sin(ph) * env
        return sig

    # Lub (primary beat at 0.08s, 55Hz) + Dub (secondary beat at 0.36s, 60Hz)
    lub = thump(0.08, 65.0, 42.0, 1.0, 0.085)
    dub = thump(0.36, 72.0, 48.0, 0.72, 0.068)
    raw = lub + dub

    # Warm low-pass filter around 135Hz for deep chest resonance
    sos = butter(4, 135.0, btype="lowpass", fs=SR, output="sos")
    filtered = sosfilt(sos, raw)
    # Gentle tail fade
    fade = np.minimum((dur - t) / 0.06, 1.0)
    filtered *= fade
    return np.column_stack([filtered, filtered])


def generate_ambient_bed(rng: np.random.Generator, ffmpeg_bin: str) -> Path:
    """485s dark, subtle cinematic D-minor ambient pad calibrated precisely to -29 dBFS."""
    dur = 485.0
    sr_bed = 24000  # Generate at 24kHz for fast synthesis, upsample smoothly to 48kHz via ffmpeg
    n = int(sr_bed * dur)
    t = np.linspace(0.0, dur, n, dtype=np.float32)

    # Dark cinematic D-minor drone harmonics (D2, A2, D3, F3, A3) with slow organic LFO breathing
    lfo1 = 0.55 + 0.45 * np.sin(2.0 * np.pi * 0.031 * t)
    lfo2 = 0.55 + 0.45 * np.sin(2.0 * np.pi * 0.019 * t + 1.3)
    lfo3 = 0.50 + 0.50 * np.sin(2.0 * np.pi * 0.013 * t + 2.7)

    # Subtle detuned stereo oscillators for rich dark cinematic space
    d2_l = 0.42 * np.sin(2.0 * np.pi * 73.42 * t)
    d2_r = 0.42 * np.sin(2.0 * np.pi * 73.50 * t + 0.4)

    a2_l = 0.28 * np.sin(2.0 * np.pi * 110.00 * t) * lfo1
    a2_r = 0.28 * np.sin(2.0 * np.pi * 110.12 * t + 0.9) * lfo1

    d3_l = 0.20 * np.sin(2.0 * np.pi * 146.83 * t) * lfo2
    d3_r = 0.20 * np.sin(2.0 * np.pi * 146.65 * t + 1.5) * lfo2

    f3_l = 0.14 * np.sin(2.0 * np.pi * 174.61 * t) * lfo3
    f3_r = 0.14 * np.sin(2.0 * np.pi * 174.82 * t + 2.1) * lfo3

    a3_l = 0.08 * np.sin(2.0 * np.pi * 220.00 * t) * (lfo1 * lfo3)
    a3_r = 0.08 * np.sin(2.0 * np.pi * 220.25 * t + 0.7) * (lfo2 * lfo3)

    # Soft dark atmospheric room noise (low-passed below 420Hz)
    sos_air = butter(3, [40.0, 420.0], btype="bandpass", fs=sr_bed, output="sos")
    air_l = sosfilt(sos_air, rng.standard_normal(n).astype(np.float32)).astype(np.float32)
    air_r = sosfilt(sos_air, rng.standard_normal(n).astype(np.float32)).astype(np.float32)
    air_l = air_l / (np.max(np.abs(air_l)) + 1e-9) * 0.10
    air_r = air_r / (np.max(np.abs(air_r)) + 1e-9) * 0.10

    left = (d2_l + a2_l + d3_l + f3_l + a3_l + air_l).astype(np.float32)
    right = (d2_r + a2_r + d3_r + f3_r + a3_r + air_r).astype(np.float32)

    # Gentle 4s fade-in and 5s fade-out
    fi = int(4.0 * sr_bed)
    fo = int(5.0 * sr_bed)
    left[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    right[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    left[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    right[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)

    # Calibrate RMS precisely to -29.0 dBFS
    rms = float(np.sqrt(0.5 * (np.mean(left ** 2) + np.mean(right ** 2)))) + 1e-12
    target_rms = 10.0 ** (-29.0 / 20.0)
    gain = target_rms / rms
    stereo = np.clip(np.column_stack([left * gain, right * gain]), -1.0, 1.0)

    tmp_wav = Path("/tmp/bg_ambient_bed.wav")
    wavfile.write(str(tmp_wav), sr_bed, (stereo * 32767.0).astype(np.int16))

    mp3_path = SFX_DIR / "bg_ambient_bed.mp3"
    subprocess.run(
        [
            ffmpeg_bin, "-y", "-i", str(tmp_wav),
            "-ar", "48000", "-ac", "2", "-b:a", "128k",
            str(mp3_path), "-loglevel", "error",
        ],
        check=True,
    )
    tmp_wav.unlink(missing_ok=True)
    return mp3_path


def main():
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    ffmpeg_bin = find_ffmpeg()

    save_stereo_wav(SFX_DIR / "whoosh.wav", generate_whoosh(rng), peak_db=-2.0)
    save_stereo_wav(SFX_DIR / "bass_hit.wav", generate_bass_hit(rng), peak_db=-1.5)
    save_stereo_wav(SFX_DIR / "riser.wav", generate_riser(rng), peak_db=-2.5)
    save_stereo_wav(SFX_DIR / "heartbeat.wav", generate_heartbeat(), peak_db=-2.0)
    mp3_path = generate_ambient_bed(rng, ffmpeg_bin)

    for p in sorted(SFX_DIR.iterdir()):
        print(f"  Generated {p.relative_to(ROOT)} ({p.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
