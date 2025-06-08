'''
Author:         Aryan Shukla
Plugin Name:    Parameters Display
Tools Used:     Python 3.13.3, XPPython3 4.5.0
'''

from XPPython3 import xp # type: ignore

class PythonInterface:
    def __init__(self):
        self.Name = "Parameters Display"
        self.Sig = "aryanshukla.plugin001.parametersdisplay"
        self.Desc = "Draws Parameters On The Screen In Both External And Internal Views"

        self.datarefs = {
            'altitude': 'sim/flightmodel2/position/pressure_altitude',
            'heading': 'sim/flightmodel/position/mag_psi',
            'pitch': 'sim/flightmodel/position/theta',
            'roll': 'sim/flightmodel/position/phi',
            'cas': 'sim/cockpit2/gauges/indicators/airspeed_kts_pilot',
            'vspd': 'sim/cockpit2/gauges/indicators/vvi_fpm_pilot',
            'n1': 'sim/flightmodel/engine/ENGN_N1_'
        }
        self.parameters = list(self.datarefs.keys())

        self.HUD_X = 0
        self.HUD_Y = 5
        self.COL_WIDTH = 75
        self.LINE_HEIGHT = 20
        self.BOX_HEIGHT = (len(self.datarefs)) * self.LINE_HEIGHT

        self.isDisplaying = False

    def StartDisplay(self):
        xp.log("Display --> Started.")
        self.isDisplaying = True
        xp.setMenuItemName(self.menuId, self.menuIndex, "Toggle: OFF")
        xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

    def StopDisplay(self):
        xp.unregisterDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)
        self.isDisplaying = False
        xp.setMenuItemName(self.menuId, self.menuIndex, "Toggle: ON")
        xp.log("Display --> Stopped.")

    def ToggleDisplay(self, menuRefCon, itemRefCon):
        if self.isDisplaying:
            self.StopDisplay()
        else:
            self.StartDisplay()

    def DrawCallback(self, inPhase, inBefore, inRefCon):
        xp.drawTranslucentDarkBox(
            self.HUD_X,
            self.BOX_HEIGHT,
            2*self.COL_WIDTH,
            self.HUD_Y
        )

        Y_OFFSET = self.BOX_HEIGHT
        for key, ref in self.datarefs_pointers.items():
            if key == 'n1':
                n1_values = [0.0, 0.0]
                xp.getDatavf(ref, n1_values, 2)

                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X,
                    self.HUD_Y + Y_OFFSET,
                    "N1A1",
                    None,
                    xp.Font_Proportional
                )
                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X + self.COL_WIDTH,
                    self.HUD_Y + Y_OFFSET,
                    f"{n1_values[0]:6.0f}",
                    None,
                    xp.Font_Proportional
                )
                Y_OFFSET -= self.LINE_HEIGHT

                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X,
                    self.HUD_Y + Y_OFFSET,
                    "N1A2",
                    None,
                    xp.Font_Proportional
                )
                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X + self.COL_WIDTH,
                    self.HUD_Y + Y_OFFSET,
                    f"{n1_values[1]:6.0f}",
                    None,
                    xp.Font_Proportional
                )
                Y_OFFSET -= self.LINE_HEIGHT

            else:
                val = xp.getDataf(ref)
                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X,
                    self.HUD_Y + Y_OFFSET,
                    key.upper(),
                    None,
                    xp.Font_Proportional
                )
                xp.drawString(
                    (1.0, 1.0, 1.0),
                    self.HUD_X + self.COL_WIDTH,
                    self.HUD_Y + Y_OFFSET,
                    f"{val:6.0f}",
                    None,
                    xp.Font_Proportional
                )
                Y_OFFSET -= self.LINE_HEIGHT

        return 1

    
    def XPluginStart(self):
        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in self.parameters
        }

        return self.Name, self.Sig, self.Desc

    def XPluginEnable(self):
        self.menuId = xp.createMenu("Display Parameters", None, 0, self.ToggleDisplay, 0)
        self.menuIndex = xp.appendMenuItem(self.menuId, "Toggle: ON", 1, 1)
        return 1

    def XPluginDisable(self):
        if hasattr(self, 'menuId') and self.menuId is not None:
            xp.destroyMenu(self.menuId)
            self.menuId = None

    def XPluginStop(self):
        return