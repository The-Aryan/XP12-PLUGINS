from XPPython3 import xp  # type: ignore
import os
import datetime


class PythonInterface:
    def __init__(self):
        self.Name = "Generate FDR Files"
        self.Sig = "aryanshukla.plugin002.generatefdr"
        self.Desc = "Logs Timeseries Data Into A FDR File"

        self.datarefs = {
            # Must Have Datarefs
            'longitude': 'sim/flightmodel/position/longitude',
            'latitude': 'sim/flightmodel/position/latitude',
            'press_altitude': 'sim/flightmodel2/position/pressure_altitude',
            'mag_heading': 'sim/flightmodel/position/mag_psi',
            'pitch': 'sim/flightmodel/position/theta',
            'roll': 'sim/flightmodel/position/phi',

            # Optional Datarefs
            'baro_altitude': 'sim/cockpit2/gauges/indicators/altitude_ft_pilot',
            'cas': 'sim/cockpit2/gauges/indicators/airspeed_kts_pilot',
            'vspd': 'sim/cockpit2/gauges/indicators/vvi_fpm_pilot',
            'slat': 'sim/flightmodel/controls/slatrat',
            'flap': 'sim/flightmodel/controls/flaprat',
            'gear_down': 'laminar/A333/fws/landing_gear_down'
        }
        self.parameters = list(self.datarefs.keys())

        self.isLogging = False
        self.sampling_rate = 1
        self.counter = 0
        self.file = None

    def StartLogging(self):
        xp.log("Logging --> Started.")

        time = datetime.datetime.now().strftime('%H:%M:%S')
        date = datetime.datetime.now().strftime('%d/%m/%Y')
        log_path = os.path.join(
            'G:\\SteamLibrary\\steamapps\\common\\X-Plane 12\\Output\\fdr_files',
            f"FDR_Log_{date + "_" + time}.fdr"
        )
        self.file = open(log_path, 'w')

        self.file.write("A\n")
        self.file.write("3\n\n")

        self.file.write("ACFT, Aircraft/Laminar Research/Airbus A330-300/A330.acf\n")
        self.file.write("TAIL, N12345\n")
        self.file.write(f"TIME, {time}\n")
        self.file.write(f"DATE, {date}\n")
        self.file.write("PRES, 29.92\n")
        self.file.write("DISA, 0\n")
        self.file.write("WIND, 180,10\n\n")
    
        for name, ref in self.datarefs.items():
            # not sure of the order in which datarefs are written when using dictionary.
            if name not in ['latitude', 'longitude', 'press_altitude', 'mag_heading', 'pitch', 'roll']:
                self.file.write(f"DREF, {ref}\t\t\t1.0\n\n")

        self.file.write("COMM,Sample,Long,Lat,PressureAlt,MagHeading,Pitch,Roll,BaroAlt,VSPD,SLAT,FLAP,LDG\n")
        self.counter = 0
        xp.registerFlightLoopCallback(self.FlightLoopCallback, self.sampling_rate, 0)
        xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window)

    def StopLogging(self):
        if self.file:
            self.file.close()
            self.file = None
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback)
        xp.unregisterDrawCallback(self.DrawCallback, 0)
        xp.log("Logging --> Stopped.")

    def ToggleLogging(self):
        label = "Toggle: ON" if self.isLogging else "Toggle: OFF"
        xp.setMenuItemName(self.menuId, 1, label)
        if self.isLogging:
            self.isLogging = False
            self.StopLogging()
        else:
            self.StartLogging()
            self.isLogging = True

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        i = self.counter
        values = [i] + [
            xp.getDataf(self.datarefs_pointers[param]) if self.datarefs_pointers.get(param) else float('nan')
            for param in self.parameters
        ]
        self.file.write("DATA," + ",".join(f"{val:.5f}" for val in values) + "\n")
        self.file.flush()
        self.counter += 1

        return 1

    def DrawCallback(self, inPhase, inIsBefore, inRefCon):
        screen_width, screen_height = xp.getScreenSize()
        xp.drawString(
            rgb=(1.0, 1.0, 1.0),
            x=screen_width + 5 - screen_width,
            y=screen_height + 5 - screen_height,
            value=f"[LOGGING TIMESERIES DATA] | Samples: {self.counter:,}",
            fontID=1
        )
        return 1

    def XPluginStart(self):

        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in self.parameters
        }

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self):
        self.menuId = xp.createMenu("genFDR", None, 0, self.ToggleLogging, 0)
        xp.appendMenuItem(self.menuId, "Toggle: OFF", 1, 1)

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def XPluginDisable(self):
        if self.isLogging:
            self.StopLogging()
        xp.destroyMenu(self.menuId)

    def XPluginStop(self):
        pass