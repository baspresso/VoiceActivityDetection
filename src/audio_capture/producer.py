import sounddevice as sd
import time
import queue
import numpy as np
import yaml
import argparse

from confluent_kafka import Producer
from src.utils.kafka_utils import get_producer_config
from src.utils.audio_utils import get_frame_size

parser = argparse.ArgumentParser(description="Capture audio from a specific device and produce to Kafka.")
parser.add_argument("--source_id", required=True, help="Unique identifier for this audio source (e.g., 'micA').")
parser.add_argument("--device", type=int, required=True, help="Device index for sounddevice.")
args = parser.parse_args()

# Load settings
with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

SAMPLE_RATE = config["sample_rate"]
FRAME_DURATION_MS = config["frame_duration_ms"]
RAW_AUDIO_TOPIC = config["raw_audio_topic"]

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    """Callback from sounddevice each time a block of audio is available."""
    audio_queue.put(indata.copy())

def main():
    producer_conf = get_producer_config()
    producer = Producer(producer_conf)
    frame_size = get_frame_size(SAMPLE_RATE, FRAME_DURATION_MS)
    print("Starting audio capture. Press Ctrl+C to stop.")
    with sd.InputStream(device=args.device,
                        channels=1,
                        samplerate=SAMPLE_RATE,
                        blocksize=frame_size,
                        callback=audio_callback):
        try:
            while True:
                frame = audio_queue.get()
                gain = 200000  # example value, adjust as needed
                amplified = frame * gain
                amplified_clamped = np.clip(amplified, -32767, 32767)
                frame_int16 = amplified_clamped.astype(np.int16)
                frame_bytes = frame_int16.tobytes()
                timestamp_key = str(int(time.time() * 1000))
                message_key = f"{args.source_id}-{timestamp_key}"
                producer.produce(
                    topic=RAW_AUDIO_TOPIC,
                    key=message_key,
                    value=frame_bytes
                )
                producer.poll(0)
        except KeyboardInterrupt:
            print("Stopping audio capture...")
        finally:
            producer.flush()

if __name__ == "__main__":
    main()