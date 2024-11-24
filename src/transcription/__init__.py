from .transcriber import Transcriber
from .youtube_loader import YouTubeLoader
import os

class VideoTranscriptionService:
    def __init__(self, api_key: str, output_dir: str = "temp"):
        self.loader = YouTubeLoader(output_dir)
        self.transcriber = Transcriber(api_key)

    def transcribe_youtube_video(self, url: str, language: str = "en") -> str:
        print(f"Transcribing video from {url}")
        audio_path = self.loader.download_and_convert(url)
        print(f"Downloaded audio to {audio_path}")
        print(f"Transcribing audio to text")
        transcription = self.transcriber.transcribe(
            audio_file_path=audio_path,
            language=language
        )
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return transcription