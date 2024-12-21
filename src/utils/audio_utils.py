import math

def get_frame_size(sample_rate, frame_duration_ms):
    """
    Convert frame duration in milliseconds
    """
    return int(sample_rate * (frame_duration_ms / 1000.0))

def stereo_to_mono(frame):
    return frame[:, 0]

def normalize_audio(audio_data):
    """
    Example normalization (peak normalization).
    """
    peak = max(abs(audio_data))
    if peak == 0:
        return audio_data
    return audio_data / peak