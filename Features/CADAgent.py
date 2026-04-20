import os
import time
import pyautogui
from pywinauto import Application, Desktop
from Features.Face.Mouth import speak

class CADAgent:
    def __init__(self):
        self.app = None
        # Common CAD process names
        self.cad_processes = ["acad.exe", "revit.exe", "MicroStation.exe"]

    def connect_to_cad(self):
        """Attempts to connect to an already running CAD instance"""
        try:
            for proc in self.cad_processes:
                try:
                    self.app = Application(backend="win32").connect(path=proc)
                    speak(f"Successfully connected to active {proc} instance.")
                    return True
                except Exception:
                    continue
            return False
        except Exception as e:
            print(f"[CADAgent] Connection Error: {e}")
            return False

    def launch_cad(self, path=None):
        """Launches CAD if not already running"""
        if not path:
            # Default to a common path or ask user
            path = r"C:\Program Files\Autodesk\AutoCAD 2024\acad.exe"
        
        if os.path.exists(path):
            speak("Launching your CAD environment. Please wait.")
            os.startfile(path)
            time.sleep(10) # Wait for splash screen
            return self.connect_to_cad()
        else:
            speak("I couldn't find your CAD executable. Please provide the correct path.")
            return False

    def execute_cad_command(self, command):
        """Sends a command to the CAD command line via keyboard emulation"""
        if not self.connect_to_cad():
            speak("CAD is not currently open or accessible.")
            return False
        
        try:
            speak(f"Executing CAD command: {command}")
            # Ensure CAD window is focused
            main_window = self.app.top_window()
            main_window.set_focus()
            
            # Send command
            pyautogui.typewrite(command)
            pyautogui.press('enter')
            return True
        except Exception as e:
            speak(f"Failed to execute CAD command: {e}")
            return False

    def zoom_extents(self):
        return self.execute_cad_command("ZOOM E")

    def save_and_close(self):
        self.execute_cad_command("QSAVE")
        speak("Drawing saved. Preparing to sync with the project hub.")

cad_agent = CADAgent()
