"""Synthetic ECG generation and signal-analysis utilities."""

from __future__ import annotations

import math
import random

from scipy import fft, signal


DEFAULT_SAMPLING_RATE = 250
DEFAULT_DURATION = 10.0


def analyze_ecg(
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    duration: float = DEFAULT_DURATION,
    noise_level: float = 0.5,
    heart_rate: float = 72.0,
    seed: int | None = None,
    include_signal: bool = False,
) -> dict:
    """Generate a synthetic P-QRS-T waveform and return JSON-safe results.

    The waveform is a simulation for demonstration and testing, not clinical data.
    """
    _validate_parameters(sampling_rate, duration, noise_level, heart_rate)
    sample_count = round(sampling_rate * duration)
    if sample_count < 15:
        raise ValueError("sampling_rate and duration must produce at least 15 samples")

    rng = random.Random(seed)
    time = [index / sampling_rate for index in range(sample_count)]
    cycle_duration = 60 / heart_rate
    ecg_signal = [
        _synthetic_beat(t % cycle_duration, cycle_duration)
        + 0.04 * math.sin(2 * math.pi * 0.33 * t)  # baseline wander
        + rng.uniform(-noise_level, noise_level)
        for t in time
    ]

    cutoff_frequency = min(20, sampling_rate * 0.4)
    b, a = signal.butter(4, cutoff_frequency / (0.5 * sampling_rate), btype="low")
    padlen = min(15, sample_count - 1)
    filtered_signal = signal.filtfilt(b, a, ecg_signal, padlen=padlen)
    window_length = min(11, sample_count if sample_count % 2 != 0 else sample_count - 1)
    if window_length <= 3:
        smoothed_signal = filtered_signal
    else:
        polyorder = min(3, window_length - 1)
        smoothed_signal = signal.savgol_filter(filtered_signal, window_length=window_length, polyorder=polyorder)

    peaks, _ = signal.find_peaks(
        smoothed_signal,
        distance=max(1, round(sampling_rate * cycle_duration * 0.5)),
        height=0.28,
    )

    detected_beats = len(peaks)
    bpm = _calculate_bpm(peaks, sampling_rate, duration)
    spectrum = fft.fft(smoothed_signal)
    analysis = {
        "detected_heartbeats": detected_beats,
        "bpm": round(bpm, 2),
        "heart_status": _heart_status(bpm),
        "peak_positions": peaks.tolist(),
        "peak_times": [round(time[index], 4) for index in peaks],
        "signal_statistics": {
            "maximum": round(float(max(smoothed_signal)), 3),
            "minimum": round(float(min(smoothed_signal)), 3),
            "average": round(float(sum(smoothed_signal) / len(smoothed_signal)), 3),
        },
        "fft_first_10": [
            {"real": round(float(value.real), 6), "imaginary": round(float(value.imag), 6)}
            for value in spectrum[:10]
        ],
        "signal_preview": _signal_preview(time, smoothed_signal),
    }
    if include_signal:
        analysis["signal"] = [round(float(value), 6) for value in smoothed_signal]

    return {
        "parameters": {
            "sampling_rate": sampling_rate,
            "duration": duration,
            "noise_level": noise_level,
            "heart_rate": heart_rate,
            "seed": seed,
        },
        "analysis": analysis,
    }


def _synthetic_beat(phase: float, cycle_duration: float) -> float:
    """Construct a P-QRS-T complex from scaled Gaussian pulses."""
    def pulse(center: float, width: float, amplitude: float) -> float:
        return amplitude * math.exp(-0.5 * ((phase - center * cycle_duration) / (width * cycle_duration)) ** 2)

    return (
        pulse(0.18, 0.045, 0.12)  # P
        + pulse(0.37, 0.012, -0.18)  # Q
        + pulse(0.40, 0.010, 1.15)  # R
        + pulse(0.43, 0.014, -0.26)  # S
        + pulse(0.68, 0.075, 0.32)  # T
    )


def _validate_parameters(sampling_rate: int, duration: float, noise_level: float, heart_rate: float) -> None:
    if not isinstance(sampling_rate, int) or sampling_rate < 50 or sampling_rate > 2_000:
        raise ValueError("sampling_rate must be an integer between 50 and 2000 Hz")
    if duration <= 0 or duration > 120:
        raise ValueError("duration must be greater than 0 and no more than 120 seconds")
    if noise_level < 0 or noise_level > 5:
        raise ValueError("noise_level must be between 0 and 5")
    if heart_rate < 30 or heart_rate > 240:
        raise ValueError("heart_rate must be between 30 and 240 BPM")


def _calculate_bpm(peaks, sampling_rate: int, duration: float) -> float:
    if len(peaks) >= 2:
        intervals = [peaks[index] - peaks[index - 1] for index in range(1, len(peaks))]
        return 60 * sampling_rate / (sum(intervals) / len(intervals))
    return len(peaks) * 60 / duration


def _heart_status(bpm: float) -> str:
    if bpm < 60:
        return "Possible Bradycardia (Low Heart Rate)"
    if bpm > 100:
        return "Possible Tachycardia (High Heart Rate)"
    return "Normal Heart Rate"


def _signal_preview(time: list[float], values, max_points: int = 600) -> list[dict]:
    """Return a compact waveform suitable for a browser chart."""
    step = max(1, math.ceil(len(values) / max_points))
    return [
        {"time": round(time[index], 4), "value": round(float(values[index]), 5)}
        for index in range(0, len(values), step)
    ]
