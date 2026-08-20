"""Command-line entry point for the ECG analyzer."""

from ecg_analyzer import analyze_ecg


if __name__ == "__main__":
    result = analyze_ecg()
    analysis = result["analysis"]
    print("\n===================================")
    print(" PURE SCIPY ECG ANALYZER")
    print("===================================\n")
    print("Signal Duration:", result["parameters"]["duration"], "seconds")
    print("Sampling Rate:", result["parameters"]["sampling_rate"], "Hz")
    print("\nDetected Heartbeats:", analysis["detected_heartbeats"])
    print("Calculated BPM:", analysis["bpm"])
    print("\nDetected Peak Positions:")
    print(analysis["peak_positions"])
    print("\nHeart Status:", analysis["heart_status"])
    print("\nSignal Statistics:")
    for name, value in analysis["signal_statistics"].items():
        print(f"{name.title()}: {value}")
