from XPPython3 import xp  # type: ignore
import threading
import speech_recognition as sr

class PythonPlugin:
    def __init__(self):
        self.Name = "VoiceCommandPlugin"
        self.Sig = "aryan.xppython.voice"
        self.Desc = "Voice control for basic aircraft functions"
        self.command_map = {
            'gear_down': 'laminar/A333/fws/landing_gear_down'
        }

    def XPluginStart(self):
        threading.Thread(target=self.listen_and_execute, daemon=True).start()
        xp.log("[VoiceCommandPlugin] Voice thread started.")
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):
        xp.log("[VoiceCommandPlugin] Stopping plugin.")

    def XPluginEnable(self):
        xp.log("[VoiceCommandPlugin] Enabled.")
        return 1

    def XPluginDisable(self):
        xp.log("[VoiceCommandPlugin] Disabled.")

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def listen_and_execute(self):
        recognizer = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception as e:
            xp.log(f"[VoiceCommandPlugin] Microphone error: {e}")
            return

        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                xp.log("[VoiceCommandPlugin] Listening...")
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                    command_text = recognizer.recognize_google(audio).lower()
                    xp.log(f"[VoiceCommandPlugin] Recognized: {command_text}")

                    if command_text in self.command_map:
                        cmd = xp.findCommand(self.command_map[command_text])
                        if cmd:
                            xp.commandOnce(cmd)
                            xp.log(f"[VoiceCommandPlugin] Executed: {self.command_map[command_text]}")
                        else:
                            xp.log(f"[VoiceCommandPlugin] Command not found: {command_text}")
                    else:
                        xp.log(f"[VoiceCommandPlugin] Unrecognized command: {command_text}")

                except sr.WaitTimeoutError:
                    continue  # just restart listening
                except sr.UnknownValueError:
                    xp.log("[VoiceCommandPlugin] Could not understand audio.")
                except Exception as e:
                    xp.log(f"[VoiceCommandPlugin] Error: {e}")
