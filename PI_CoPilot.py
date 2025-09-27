"""
Author:         Aryan Shukla
Plugin Name:    AI Co-Pilot
Tools Used:     Python 3.13.3, XPPython3 4.5.0
"""

import os
import time
from XPPython3 import xp  # type: ignore
import speech_recognition as sr
import threading
from queue import Queue

class PythonInterface:
    def __init__(self):
        self.Name = "AI CoPilot"
        self.Sig = "plugin004.aicopilot.byaryanshukla"
        self.Desc = "Voice command interface for X-Plane"

        self.parameters = {
            "GSD": "sim/cockpit/switches/gear_handle_status"
        }
        self.datarefs_pointer = {}

        self.hotkeyPress = None
        self.hotkeyRelease = None

        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            self.microphone = None
            self.DebugLog(f"[AI CoPilot] [MicInit] Failed to initialize mic: {e}")

        self.recognizer = sr.Recognizer()
        self.isRecording = False
        self.audioData = Queue()

        self.logFile = os.path.join(
            xp.getSystemPath(), "Resources", "plugins", "recording_debug.log"
        )

    def XPluginStart(self):

        self.datarefs_pointer = {
            param: xp.findDataRef(dataref) for param, dataref in self.parameters.items()
        }

        self.hotkeyPress = xp.registerHotKey(
            xp.VK_Z,
            xp.DownFlag,
            "Push-to-Talk -> Press",
            self.OnPressCallback
        )
        self.hotkeyRelease = xp.registerHotKey(
            xp.VK_Z,
            xp.UpFlag,
            "Push-to-Talk -> Release",
            self.OnReleaseCallback
        )

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self): 
        return 1
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def XPluginStop(self):
        xp.unregisterHotKey(self.hotkeyPress)
        xp.unregisterHotKey(self.hotkeyRelease)

    def XPluginDisable(self):
        pass

    def OnPressCallback(self, inRefcon):
        if not self.isRecording and self.microphone:
            xp.speakString("Started Listening")
            self.StartRecording()

    def OnReleaseCallback(self, inRefcon):
        if self.isRecording:
            xp.speakString("Stopped Listening")
            self.isRecording = False

    def StartRecording(self):
        self.DebugLog("record()")
        def record():
            try:
                self.isRecording = True
                self.DebugLog("self.isRecording = True")
                self.DebugLog("Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(self.microphone, duration=0.1)
                self.DebugLog("Mic ready, listening...")
                audio = self.recognizer.listen(self.microphone, timeout=1, phrase_time_limit=5)
                self.DebugLog(f"Finished listening. Captured {len(audio.get_raw_data())} bytes")

                if self.isRecording:
                    self.audioData = audio

                self.DebugLog("record()")

            except Exception as e:
                self.DebugLog(f"Recording error: {e}")

            finally:
                self.isRecording = False

        threading.Thread(target=record, daemon=True, name="RecordThread").start()
    
    def DebugLog(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        thread_name = threading.current_thread().name
        line = f"[{timestamp}] [{thread_name}] {msg}\n"

        xp.log(line.strip())

        with open(self.logFile, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()