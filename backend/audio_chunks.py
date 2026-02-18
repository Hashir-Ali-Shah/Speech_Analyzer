from pydub import AudioSegment , silence   
from io import BytesIO   

class AudioChunker:
    def __init__(self,min_silence_len:int=400,silence_thresh:int=0.40,keep_silence:int=200,format:str="wav"):
        self.min_silence_len = min_silence_len
        self.silence_thres = silence_thres
        self.keep_silence = keep_silence

    def split_audio_bytes(self,audio_bytes:bytes)->list[bytes]:
        audio=AudioSegment.from_file(BytesIO(audio_bytes),format=format)

        chunks=silence.split_on_silence(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=keep_silence
        )
  
  

