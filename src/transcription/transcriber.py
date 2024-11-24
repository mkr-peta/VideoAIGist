from openai import OpenAI


class Transcriber:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, audio_file_path: str, language: str = "en", 
                   model: str = "whisper-1", temperature: float = 0.0)-> str:
        # transcribe the audio files using whisper
        try:
            with open(audio_file_path, "rb") as f:
                transcription = self.client.audio.transcriptions.create(
                                    model=model, 
                                    language=language,
                                    temperature=temperature,
                                    file=f
                                )
                return transcription.text

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")