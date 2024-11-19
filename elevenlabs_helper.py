from elevenlabs import ElevenLabs, VoiceSettings, save


class ElevenLabsHelper:
    def __init__(self):
        self.client = ElevenLabs(api_key="ELEVENLABS_TOKEN")

    def clone_voice(self, name, files):
        voice = self.client.clone(
            name=name,
            description="New voice",  # Optional
            files=files,
        )
        return voice

    def tts(self, text, voice, model="eleven_multilingual_v2",
            voice_settings=VoiceSettings(stability=0, similarity_boost=1, style=1,
                                         use_speaker_boost=True)):
        audio = self.client.generate(
            text=text, voice=voice,
            model=model,
            voice_settings=voice_settings)
        return audio

    def save_audio(self, audio, path):
        save(audio, path)
        return path

    def delete_voice(self, voice_id):
        self.client.voices.delete(voice_id)