from pydub import AudioSegment, silence
from io import BytesIO


class AudioChunker:
    def __init__(self, min_silence_len: int = 400, silence_thresh: int = -40,
                 keep_silence: int = 200, fmt: str = "webm"):
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.keep_silence = keep_silence
        self.fmt = fmt

    def split_audio_bytes(self, audio_bytes: bytes) -> tuple[list[dict], float]:
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format=self.fmt)
        duration_ms = len(audio)

        chunks = silence.split_on_silence(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            keep_silence=self.keep_silence,
        )

        if not chunks:
            buf = BytesIO()
            audio.export(buf, format="wav")
            return [{"start_time": 0, "end_time": duration_ms, "audio_bytes": buf.getvalue()}], duration_ms

        output_chunks = []
        search_start = 0

        for chunk in chunks:
            chunk_duration = len(chunk)

            buf = BytesIO()
            chunk.export(buf, format="wav")
            wav_bytes = buf.getvalue()

            start_time = search_start
            end_time = start_time + chunk_duration
            search_start = end_time

            output_chunks.append({
                "start_time": start_time,
                "end_time": end_time,
                "audio_bytes": wav_bytes,
            })

        return output_chunks, duration_ms
