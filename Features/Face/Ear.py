'''
pause_threshold: seconds to wait after the user stops speaking before cutting off.
timeout: max seconds to wait for the user to start speaking (None = wait forever).
phrase_time_limit: max seconds the user can speak per utterance.
'''
import sys

try:
    import speech_recognition as sr
    try:
        from googletrans import Translator
        HAS_TRANSLATOR = True
    except (ImportError, AttributeError):
        HAS_TRANSLATOR = False
    HAS_EAR = True
except ImportError:
    HAS_EAR = False
    HAS_TRANSLATOR = False


def listen(time=5):
    if not HAS_EAR:
        return ""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source)
            r.pause_threshold = 1
            audio = r.listen(source, timeout=10, phrase_time_limit=time)
    except sr.WaitTimeoutError:
        return ""
    except OSError as e:
        print(f"[Ear] Microphone error: {e}")
        return ""

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en", pfilter=1)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[Ear] Speech recognition service error: {e}")
        return ""

    return str(query).lower()


def translation(text):
    if not HAS_TRANSLATOR:
        print(f"\nYou : {text}")
        return text
    try:
        t = Translator()
        result = t.translate(str(text))
        data = result.text
        print(f"\nYou : {data}")
        return data
    except Exception as e:
        print(f"[Ear] Translation error: {e}")
        return text


def understand(time=5):
    query = listen(time)
    return translation(query)
