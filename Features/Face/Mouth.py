import os
import tempfile
import threading

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

_active_user: str | None = None
_user_lock = threading.Lock()


def set_user(user_name: str):
    global _active_user
    with _user_lock:
        _active_user = user_name


def _get_user() -> str | None:
    with _user_lock:
        return _active_user


def speak(text: str):
    print(f"\nElio : {text}")

    if os.getenv("ELIO_HEADLESS") == "true":
        return

    user = _get_user()

    # Attempt advanced voice synthesis if server TTS is available
    try:
        from server.voice_provider import synthesize_wav, tts_ready
        if tts_ready(user):
            audio_data = synthesize_wav(text, user_name=user)
            if audio_data and HAS_PYGAME:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(audio_data)
                    temp_path = f.name
                try:
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                finally:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                return
    except Exception as e:
        print(f"[Mouth] Advanced TTS failed: {e}. Falling back to pyttsx3.")

    # Fallback to local pyttsx3
    if not HAS_PYTTSX3:
        return
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        if user == "alex" or not voices:
            voice_id = voices[0].id if voices else None
        elif user == "sandra" and len(voices) > 1:
            voice_id = voices[1].id
        else:
            voice_id = voices[0].id if voices else None
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Mouth] pyttsx3 error: {e}")
