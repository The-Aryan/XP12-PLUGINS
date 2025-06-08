from XPPython3 import xp # type: ignore

class PythonInterface:
    def __init__(self):
        self.Name = "Parameters Display"
        self.Sig = "aryanshukla.plugin001.parameterdisplay"
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

        self.HUD_X = 50
        self.HUD_Y = 500
        self.LINE_SPACING = 20

        self.isDisplaying = False

    def StartDisplay(self):
        xp.log("Display --> Started.")
        self.isDisplaying = True
        xp.setMenuItemName(self.menuId, self.menuIndex, "Toggle: OFF")
        # xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

    def StopDisplay(self):
        # xp.unregisterDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)
        self.isDisplaying = False
        xp.setMenuItemName(self.menuId, self.menuIndex, "Toggle: ON")
        xp.log("Display --> Stopped.")

    def ToggleDisplay(self, menuRefCon, itemRefCon):
        if self.isDisplaying:
            self.StopDisplay()
        else:
            self.StartDisplay()

    def DrawCallback(self, inPhase, inAfter, inRefCon):
        data = self.get_data()
        sw, sh = xp.getScreenSize()
        hud_x = self.HUD_X
        hud_y = sh - self.HUD_Y

        xp.drawTranslucentDarkBox(hud_x - 10, hud_y + 15, hud_x + 220, hud_y - 90)

        col_white = (1.0, 1.0, 1.0)
        col_green = (0.0, 1.0, 0.0)
        col_yellow = (1.0, 1.0, 0.0)
        col_red = (1.0, 0.0, 0.0)

        airspeed_color = col_green if data["Airspeed"] < 250 else col_yellow
        xp.drawString(airspeed_color, hud_x, hud_y, f"Airspeed: {data['Airspeed']:6.1f} kt", None, xp.Font_Basic)

        xp.drawString(col_white, hud_x, hud_y - self.LINE_SPACING, f"Altitude: {data['Altitude']:6.0f} ft", None, xp.Font_Basic)

        vs_color = col_green if abs(data["Vertical Speed"]) < 1000 else col_yellow
        xp.drawString(vs_color, hud_x, hud_y - 2 * self.LINE_SPACING, f"V/S: {data['Vertical Speed']:6.0f} fpm", None, xp.Font_Basic)

        n1a1_color = col_green if data["N1A1"] < 90 else col_red
        xp.drawString(n1a1_color, hud_x, hud_y - 3 * self.LINE_SPACING, f"N1A1: {data['N1A1']:6.0f}%", None, xp.Font_Basic)

        n1a2_color = col_green if data["N1A2"] < 90 else col_red
        xp.drawString(n1a2_color, hud_x, hud_y - 4 * self.LINE_SPACING, f"N1A2: {data['N1A2']:6.0f}%", None, xp.Font_Basic)

        return 1
    
    def XPluginStart(self):
        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in self.parameters
        }

        return self.Name, self.Sig, self.Desc

    def XPluginEnable(self):
        self.menuId = xp.createMenu("disParam", None, 0, self.ToggleLogging, 0)
        self.menuIndex = xp.appendMenuItem(self.menuId, "Toggle: ON", 1, 1)
        return 1

    def XPluginDisable(self):
        if hasattr(self, 'menuId') and self.menuId is not None:
            xp.destroyMenu(self.menuId)
            self.menuId = None

    def XPluginStop(self):
        return