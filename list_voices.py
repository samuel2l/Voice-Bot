from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def list_available_voices():
    """List all available ElevenLabs voices"""
    voices = elevenlabs_client.voices.get_all()
    
    print("\n=== Available ElevenLabs Voices ===\n")
    for voice in voices.voices:
        print(f"Name: {voice.name}")
        print(f"Voice ID: {voice.voice_id}")
        print(f"Category: {voice.category}")
        print(f"Description: {voice.description if hasattr(voice, 'description') else 'N/A'}")
        print(f"Labels: {voice.labels if hasattr(voice, 'labels') else 'N/A'}")
        print("-" * 60)

if __name__ == "__main__":
    list_available_voices()