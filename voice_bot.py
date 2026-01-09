import logging
from typing import Type
import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)
from openai import OpenAI
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import time
import subprocess

from dotenv import load_dotenv
import os
load_dotenv()

aai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
openai_client = OpenAI(api_key=openai_api_key)
elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)

full_transcript = [
    {"role": "system", "content": "You are a helpful assistant. Be resourceful and efficient."},
]

is_processing = False
last_transcript = ""
response_cooldown = 0


def play_audio(file_path: str):
    """Play audio file using mpv"""
    try:
        subprocess.run(
            ["mpv", file_path, "--no-video"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        print("Audio playback completed\n")
    except subprocess.CalledProcessError:
        print("Error playing audio file")
    except FileNotFoundError:
        print("mpv not found. Please install it with: brew install mpv")


def text_to_speech_file(text: str) -> str:
    """Convert text to speech and save as MP3 file"""
    start_time = time.perf_counter()
    
    response = elevenlabs_client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )
    
    save_file_path = "response.mp3"
    
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    print(f"\n{save_file_path}: saved successfully")
    print(f"TTS generation time: {elapsed:.2f} seconds")
    
    return save_file_path


def generate_ai_response(transcript_text: str):
    """Generate AI response using OpenAI and convert to speech"""
    global full_transcript, is_processing, response_cooldown
    
    # Add user message to conversation
    full_transcript.append({"role": "user", "content": transcript_text})
    print(f"\nUser: {transcript_text}")
    
    # Generate response from OpenAI
    print("Generating response...")
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=full_transcript
    )
    
    ai_response = response.choices[0].message.content
    print(f"Assistant: {ai_response}")
    
    # Add assistant response to conversation history
    full_transcript.append({"role": "assistant", "content": ai_response})
    
    # Convert response to speech
    print("Converting to speech...")
    audio_file = text_to_speech_file(ai_response)
    

    print("Playing response...")
    play_audio(audio_file)
    
    # Set cooldown period (in seconds since epoch)
    # This prevents processing audio for 3 seconds after playback
    response_cooldown = time.time() + 3
    
    is_processing = False
    print("Listening...\n")


def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")
    print("\nListening...\n")


def on_turn(self: Type[StreamingClient], event: TurnEvent):
    """Handle completed turns (end of speech)"""
    global is_processing, last_transcript, response_cooldown
    
    current_time = time.time()
    
    # Skip if:
    # 1. Already processing
    # 2. No transcript content
    # 3. Same as last transcript (duplicate)
    # 4. Within cooldown period after audio playback
    if is_processing:
        print(f"[Busy - ignoring: {event.transcript}]")
        return
    
    if not event.end_of_turn or not event.transcript.strip():
        return
    
    if event.transcript == last_transcript:
        print(f"[Duplicate - ignoring: {event.transcript}]")
        return
    
    if current_time < response_cooldown:
        print(f"[Cooldown - ignoring: {event.transcript}]")
        return
    
    # Process the transcript
    print(f"\nTranscript: {event.transcript}")
    last_transcript = event.transcript
    is_processing = True
    
    # Generate AI response
    generate_ai_response(event.transcript)


def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    print(
        f"\nSession terminated: {event.audio_duration_seconds} seconds of audio processed"
    )


def on_error(self: Type[StreamingClient], error: StreamingError):
    print(f"Error occurred: {error}")


def main():
    global streaming_client
    
    print("Starting AI Voice Assistant...")
    print("Speak into your microphone. The assistant will respond after you finish speaking.")
    print("Press Ctrl+C to stop.\n")
    
    streaming_client = StreamingClient(
        StreamingClientOptions(
            api_key=aai_api_key,
            api_host="streaming.assemblyai.com",
        )
    )
    
    streaming_client.on(StreamingEvents.Begin, on_begin)
    streaming_client.on(StreamingEvents.Turn, on_turn)
    streaming_client.on(StreamingEvents.Termination, on_terminated)
    streaming_client.on(StreamingEvents.Error, on_error)
    
    streaming_client.connect(
        StreamingParameters(
            sample_rate=16000,
            format_turns=True,
  
            
        )
    )
    
    try:
        streaming_client.stream(
            aai.extras.MicrophoneStream(sample_rate=16000)
        )
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        streaming_client.disconnect(terminate=True)


if __name__ == "__main__":
    main()