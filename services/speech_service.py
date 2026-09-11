from openai import OpenAI


class SpeechService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe(self, file_path: str) -> str:
        with open(file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="uz",
            )
        return transcript.text.strip()
