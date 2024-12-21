import yaml
import time
import numpy as np
import torch
from confluent_kafka import Consumer, Producer

from src.models.vad_pipeline_init import get_vad_pipeline
from src.utils.kafka_utils import get_consumer_config, get_producer_config
from src.utils.audio_utils import get_frame_size

with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

SAMPLE_RATE = config["sample_rate"]
FRAME_DURATION_MS = config["frame_duration_ms"]
RAW_AUDIO_TOPIC = config["raw_audio_topic"]
VAD_DECISIONS_TOPIC = config["vad_decisions_topic"]

def main():
    consumer_conf = get_consumer_config("vad_group")
    consumer = Consumer(consumer_conf)
    consumer.subscribe([RAW_AUDIO_TOPIC])
    producer_conf = get_producer_config()
    producer = Producer(producer_conf)
    vad_pipeline = get_vad_pipeline()
    chunk_duration_sec = 1.0 # 1 sec
    frames_per_chunk = int(chunk_duration_sec / (FRAME_DURATION_MS / 1000))
    frame_size = get_frame_size(SAMPLE_RATE, FRAME_DURATION_MS)
    audio_buffer = np.array([], dtype=np.int16)
    keys_buffer = []
    try:
        print("Starting VAD consumer...")
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                continue

            frame_bytes = msg.value()
            print("Consumed message size:", len(frame_bytes))
            frame_int16 = np.frombuffer(frame_bytes, dtype=np.int16)
            print("Consumer int16 stats:", frame_int16.min(), frame_int16.max(), frame_int16.mean())
            frame_key = msg.key().decode("utf-8")
            frame = np.frombuffer(frame_bytes, dtype=np.int16)

            print("Consumer frame stats:", frame.min(), frame.max(), frame.mean())

            audio_buffer = np.concatenate((audio_buffer, frame))
            keys_buffer.append(frame_key)

            if len(audio_buffer) >= frames_per_chunk * frame_size:
                # Extract exactly 1 second
                chunk = audio_buffer[: frames_per_chunk * frame_size]
                audio_buffer = audio_buffer[frames_per_chunk * frame_size :]
                waveform = torch.tensor(chunk, dtype=torch.float32).unsqueeze(0)
                
                vad_result = vad_pipeline(
                    {
                        "waveform": waveform,
                        "sample_rate": SAMPLE_RATE
                    }
                )
                if len(list(vad_result.itersegments())) > 0:
                    decision = "speech"
                else:
                    decision = "silence"
                median_key = keys_buffer[len(keys_buffer) // 2]
                keys_buffer = []

                result_msg = {
                    "timestamp": median_key,
                    "vad_label": decision
                }
                producer.produce(
                    topic=VAD_DECISIONS_TOPIC,
                    key=median_key,
                    value=str(result_msg)
                )
                producer.poll(0)

    except KeyboardInterrupt:
        print("Stopping VAD consumer...")
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    main()