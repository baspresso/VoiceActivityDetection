from pyannote.audio.pipelines import VoiceActivityDetection

def get_vad_pipeline():
    pipeline = VoiceActivityDetection(segmentation="pyannote/segmentation")
    pipeline.onset = 0.3
    pipeline.offset = 0.3

    return pipeline