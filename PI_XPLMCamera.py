from XPPython3 import xp # type: ignore
import math

isCameraControlled = False
angle = 0.0
hotkey_id = None

def camera_handler(outCameraPosition, is_losing_control, refcon):
    
    global angle
    xp.log(outCameraPosition)

    if is_losing_control:
        print("Camera control lost")
        return 0
    
    radius = 50
    angle += 0.01

    outCameraPosition[0] = radius * math.cos(angle)
    outCameraPosition[1] = 10
    outCameraPosition[2] = radius * math.sin(angle)
    outCameraPosition[3] = 0.0
    outCameraPosition[4] = math.degrees(angle)
    outCameraPosition[5] = 0.0
    return 1

def toggle_camera_control(refcon):
    global isCameraControlled
    if not isCameraControlled:
        print("Camera control activating...")
        xp.controlCamera(xp.ControlCameraUntilViewChanges, camera_handler, None)
    else:
        print("Releasing Camera control...")
        xp.dontControlCamera()
        
    isCameraControlled = True

class PythonInterface:
    def XPluginStart(self):
        global hotkey_id
        hotkey_id = xp.registerHotKey(
            xp.VK_C,
            xp.DownFlag,
            "Toggle Camera Control",
            toggle_camera_control,
        )
        return "CameraControlXP", "aryan.shukla.plugin003.CameraControl", "XPLMCamera Control Example"
    
    def XPluginStop(self):
        global hotkey_id, isCameraControlled
        if isCameraControlled:
            xp.dontControlCamera()
            isCameraControlled = False
        if hotkey_id:
            xp.unregisterHotKey(hotkey_id)
            hotkey_id = None
    
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        global isCameraControlled
        if isCameraControlled:
            xp.dontControlCamera()
            isCameraControlled = False
    
    def XPluginReceiveMessage(in_from_who, in_message, in_param):
        pass