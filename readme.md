# AI Voice Assistant

A real-time voice-powered AI assistant that uses speech-to-text, natural language processing, and text-to-speech to create seamless conversational interactions.

## 🎯 Overview

This voice assistant listens to your speech in real-time, transcribes it, generates intelligent responses using OpenAI's GPT models, and speaks back to you with natural-sounding voice synthesis. The system maintains conversation context for coherent multi-turn dialogues.

## ✨ Features

- **Real-time Speech Recognition** - Powered by AssemblyAI's Universal Streaming model
- **Natural Language Understanding** - Uses OpenAI GPT-4o-mini for intelligent responses
- **High-Quality Voice Synthesis** - ElevenLabs text-to-speech with customizable voices
- **Conversation Memory** - Maintains context across multiple turns
- **Low Latency Audio Playback** - Fast response times using mpv
- **Anti-Feedback Protection** - Prevents the assistant from responding to its own voice
- **Configurable Settings** - Easy voice selection and customization

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Voice Assistant Pipeline                      │
└─────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  Microphone  │
    │    Input     │
    └──────┬───────┘
           │ Audio Stream
           ▼
    ┌──────────────────────┐
    │   AssemblyAI API     │
    │  (Speech-to-Text)    │
    │  - Real-time stream  │
    │  - Turn detection    │
    └──────┬───────────────┘
           │ Transcript
           ▼
    ┌──────────────────────┐
    │   Conversation       │
    │   Manager            │
    │  - History tracking  │
    │  - Duplicate filter  │
    └──────┬───────────────┘
           │ User Message
           ▼
    ┌──────────────────────┐
    │    OpenAI API        │
    │   (GPT-4o-mini)      │
    │  - Response gen      │
    │  - Context aware     │
    └──────┬───────────────┘
           │ AI Response
           ▼
    ┌──────────────────────┐
    │   ElevenLabs API     │
    │  (Text-to-Speech)    │
    │  - Voice synthesis   │
    │  - MP3 generation    │
    └──────┬───────────────┘
           │ Audio File
           ▼
    ┌──────────────────────┐
    │   Audio Player       │
    │      (mpv)           │
    │  - Low latency       │
    │  - Speed control     │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────┐
    │   Speakers   │
    │    Output    │
    └──────────────┘
```

### Component Architecture

#### 1. **Audio Input Layer**

**Component:** `aai.extras.MicrophoneStream`

- Captures audio from the system microphone
- Samples at 16kHz (optimized for speech recognition)
- Streams audio chunks in real-time to AssemblyAI

**Key Configuration:**
```python
microphone_stream = aai.extras.MicrophoneStream(sample_rate=16000)
```

#### 2. **Speech Recognition Layer**

**Component:** AssemblyAI Streaming Client (v3)

**Features:**
- Real-time transcription with minimal latency
- Universal model for high accuracy across accents and contexts
- Turn-based detection (automatically detects when user stops speaking)
- End-of-turn events for natural conversation flow

**Architecture:**
```python
StreamingClient(
    StreamingClientOptions(
        api_key=aai_api_key,
        api_host="streaming.assemblyai.com",
    )
)

StreamingParameters(
    sample_rate=16000,
    format_turns=True,  # Enables turn detection
)
```

**Event Handlers:**
- `on_begin` - Session initialization
- `on_turn` - Processes completed speech segments
- `on_error` - Error handling
- `on_terminated` - Cleanup on session end

#### 3. **Conversation Management Layer**

**Component:** Custom conversation manager with state tracking

**Key Features:**

a. **Conversation History:**
```python
full_transcript = [
    {"role": "system", "content": "You are a helpful assistant..."},
    {"role": "user", "content": "User message"},
    {"role": "assistant", "content": "AI response"},
    # ... continues
]
```

b. **Anti-Feedback System:**
- **Processing Flag:** Prevents simultaneous response generation
- **Cooldown Timer:** 3-second window after audio playback to ignore microphone input
- **Duplicate Detection:** Tracks last transcript to avoid reprocessing identical text
- **Turn Validation:** Only processes complete turns with actual content

**Protection Logic:**
```python
if is_processing:
    # Ignore - already generating response
if current_time < response_cooldown:
    # Ignore - within cooldown period
if event.transcript == last_transcript:
    # Ignore - duplicate transcript
```

#### 4. **Natural Language Processing Layer**

**Component:** OpenAI GPT-4o-mini

**Features:**
- Context-aware responses using full conversation history
- Fast inference time for real-time conversations
- Cost-effective for production use

**API Call:**
```python
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=full_transcript  # Includes full context
)
```

#### 5. **Voice Synthesis Layer**

**Component:** ElevenLabs Text-to-Speech API

**Features:**
- High-quality, natural-sounding voices
- Low-latency streaming model (eleven_turbo_v2_5)
- Customizable voice parameters
- Multiple voice options (male/female, various accents)

**Voice Settings:**
```python
VoiceSettings(
    stability=0.0,          # Voice consistency
    similarity_boost=1.0,   # Voice clarity
    style=0.0,              # Expressiveness
    use_speaker_boost=True, # Enhanced audio quality
    speed=1.0,              # Playback speed
)
```

**Output Format:**
- Format: MP3 (22.05kHz, 32kbps)
- Optimized for speech clarity and small file size

#### 6. **Audio Playback Layer**

**Component:** mpv media player

**Why mpv?**
- Ultra-low latency (100-300ms faster than VLC)
- Lightweight with minimal overhead
- Scriptable with extensive control options
- No GUI overhead in command-line mode

**Playback Command:**
```python
subprocess.run(
    ["mpv", file_path, "--no-video"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```

### Data Flow Diagram

```
User Speaks
    │
    ├─► [Microphone Stream] ──► Raw Audio (PCM)
    │
    ├─► [AssemblyAI] ──► Partial Transcripts
    │                      │
    │                      ├─► End of Turn Detected
    │                      │
    │                      └─► Final Transcript
    │
    ├─► [State Manager] ──► Validation
    │                         ├─► Not processing? ✓
    │                         ├─► Not in cooldown? ✓
    │                         ├─► Not duplicate? ✓
    │                         └─► Has content? ✓
    │
    ├─► [Conversation History] ──► Add user message
    │
    ├─► [OpenAI API] ──► Generate response
    │                      │
    │                      └─► AI text response
    │
    ├─► [Conversation History] ──► Add assistant message
    │
    ├─► [ElevenLabs API] ──► Synthesize speech
    │                         │
    │                         └─► MP3 audio file
    │
    ├─► [mpv Player] ──► Audio playback
    │
    └─► [Cooldown Timer] ──► Set 3-second wait
                              │
                              └─► Ready for next input
```

### State Management

The system uses several state variables to ensure smooth operation:

```python
# Prevents concurrent processing
is_processing: bool = False

# Stores last transcript to detect duplicates
last_transcript: str = ""

# Timestamp when system can accept new input
response_cooldown: float = 0

# Full conversation context
full_transcript: List[Dict] = [...]
```

### Event Loop

```
┌─────────────────────────────────────┐
│  Microphone continuously streams    │
│  audio to AssemblyAI                │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  AssemblyAI sends partial           │
│  transcripts (ignored)              │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  User stops speaking                │
│  ➜ End-of-turn event triggered      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  on_turn() handler validates:       │
│  • is_processing == False           │
│  • Not in cooldown                  │
│  • Not duplicate                    │
│  • Has content                      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Set is_processing = True           │
│  Call generate_ai_response()        │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  OpenAI generates response          │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  ElevenLabs converts to speech      │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  mpv plays audio                    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Set response_cooldown = now + 3s   │
│  Set is_processing = False          │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  System ready for next input        │
│  (loops back to top)                │
└─────────────────────────────────────┘
```

## 🚀 Setup

### Prerequisites

- Python 3.8+
- macOS (for mpv installation via Homebrew)
- Microphone and speakers
- API keys for:
  - AssemblyAI
  - OpenAI
  - ElevenLabs

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd voice-assistant
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv myenv
source myenv/bin/activate  # On macOS/Linux
```

3. **Install Python dependencies:**
```bash
pip install assemblyai
pip install "assemblyai[extras]"
pip install openai
pip install elevenlabs
pip install python-dotenv
```

4. **Install system dependencies:**
```bash
# Install PortAudio (required for microphone access)
brew install portaudio

# Install mpv (audio player)
brew install mpv
```

5. **Set up environment variables:**

Create a `.env` file in the project root:
```env
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
```

### Getting API Keys

1. **AssemblyAI:** Sign up at [assemblyai.com](https://www.assemblyai.com/)
2. **OpenAI:** Get your key from [platform.openai.com](https://platform.openai.com/)
3. **ElevenLabs:** Register at [elevenlabs.io](https://elevenlabs.io/)

## 📖 Usage

### Basic Usage

Run the voice assistant:
```bash
python voice_assistant.py
```

The assistant will:
1. Start listening to your microphone
2. Wait for you to speak
3. Transcribe your speech when you pause
4. Generate an intelligent response
5. Speak the response back to you
6. Return to listening mode

### Stopping the Assistant

Press `Ctrl+C` to stop the assistant gracefully.

### Customizing the Voice

List available voices:
```bash
python list_voices.py
```

Update the `ELEVENLABS_VOICE_ID` in your `.env` file with your preferred voice ID.

## 🎛️ Configuration

### Voice Settings

Modify `VoiceSettings` in the `text_to_speech_file()` function:

```python
VoiceSettings(
    stability=0.0,           # 0.0-1.0: Lower = more variable
    similarity_boost=1.0,    # 0.0-1.0: Higher = clearer
    style=0.0,               # 0.0-1.0: Expressiveness
    use_speaker_boost=True,  # Enhanced audio quality
    speed=1.0,               # 0.25-4.0: Playback speed
)
```

### System Prompt

Customize the AI's personality in the `full_transcript` initialization:

```python
full_transcript = [
    {"role": "system", "content": "Your custom instructions here"},
]
```

### Cooldown Period

Adjust the cooldown time after responses (in seconds):

```python
response_cooldown = time.time() + 3  # Change 3 to your preferred duration
```

### Audio Playback Speed

Modify the `play_audio()` function:

```python
def play_audio(file_path: str, speed: float = 1.5):  # 1.5x speed
    subprocess.run(
        ["mpv", file_path, "--no-video", f"--speed={speed}"],
        # ...
    )
```

## 🔧 Advanced Features

### Voice Selection Script

Create `list_voices.py`:
```python
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

voices = client.voices.get_all()
for voice in voices.voices:
    print(f"{voice.name}: {voice.voice_id}")
```

### Conversation History Persistence

Add conversation saving:
```python
import json

def save_conversation():
    with open("conversation_history.json", "w") as f:
        json.dump(full_transcript, f, indent=2)

def load_conversation():
    try:
        with open("conversation_history.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"role": "system", "content": "..."}]
```

## 🐛 Troubleshooting

### "Module 'assemblyai' has no attribute 'RealtimeModel'"

**Solution:** Update to the latest AssemblyAI library:
```bash
pip install --upgrade assemblyai
```

### "mpv not found"

**Solution:** Install mpv:
```bash
brew install mpv
```

### Memory Corruption Error

**Solution:** Don't manually stop/start the microphone stream. Let it run continuously.

### Assistant Responds to Its Own Voice

**Solution:** The system has built-in cooldown protection. If issues persist:
- Increase `response_cooldown` duration
- Use headphones to prevent speaker feedback
- Adjust microphone sensitivity in system settings

### Audio Not Playing

**Solution:**
1. Check mpv installation: `which mpv`
2. Test manually: `mpv response.mp3`
3. Check system audio output settings

### High API Costs

**Solution:**
- Use `gpt-4o-mini` instead of `gpt-4` (already configured)
- Implement conversation length limits
- Add cost tracking and warnings

## 📊 Performance Optimization

### Latency Breakdown

Typical response times:
- Speech recognition: ~100-500ms (real-time streaming)
- OpenAI response: ~500-2000ms (depends on response length)
- Voice synthesis: ~500-1500ms (depends on text length)
- Audio playback: ~50-200ms
- **Total: ~1.2-4.2 seconds**

### Optimization Tips

1. **Use smaller models:**
   - GPT-4o-mini is already optimized for speed
   - Consider streaming responses for longer outputs

2. **Pre-cache common responses:**
   ```python
   common_responses = {
       "hello": "cached_hello.mp3",
       "goodbye": "cached_goodbye.mp3",
   }
   ```

3. **Reduce audio quality for speed:**
   ```python
   output_format="mp3_22050_16",  # Lower bitrate
   ```

## 🔐 Security Best Practices

1. **Never commit `.env` file:**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use environment-specific keys:**
   - Development keys for testing
   - Production keys for deployment

3. **Implement rate limiting:**
   ```python
   from time import sleep
   
   # Prevent API abuse
   sleep(0.5)  # Minimum time between requests
   ```

4. **Monitor API usage:**
   - Set up billing alerts
   - Track API call counts
   - Implement usage limits

## 📝 Project Structure

```
voice-assistant/
│
├── voice_assistant.py      # Main application
├── list_voices.py          # Voice selection utility
├── .env                    # Environment variables (not in git)
├── .gitignore             # Git ignore file
├── README.md              # This file
├── requirements.txt       # Python dependencies
│
├── myenv/                 # Virtual environment (not in git)
│
└── response.mp3          # Generated audio (temporary)
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **AssemblyAI** - Real-time speech recognition
- **OpenAI** - Natural language processing
- **ElevenLabs** - High-quality voice synthesis
- **mpv** - Lightweight audio playback

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review API documentation:
  - [AssemblyAI Docs](https://www.assemblyai.com/docs)
  - [OpenAI API Docs](https://platform.openai.com/docs)
  - [ElevenLabs API Docs](https://elevenlabs.io/docs)

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Wake word detection ("Hey Assistant")
- [ ] Conversation history UI
- [ ] Voice activity detection improvements
- [ ] WebSocket-based streaming for lower latency
- [ ] Custom voice training integration
- [ ] Emotion detection and response
- [ ] Multi-user support with voice identification
- [ ] Integration with smart home devices
- [ ] Mobile app version

---

**Built with ❤️ for seamless human-AI voice interaction**