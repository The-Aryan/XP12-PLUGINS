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

        self.isLogging = [False]
        self.isDrawing = [False]
        self.sampling_rate = 1
        self.counter = [0]
        self.file = [None]

    def XPluginStart(self):

        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in self.parameters
        }

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self):
        self.menu_handler = xp.createMenu("genFDR", None, 0, self.ToggleLogging, 0)
        xp.appendMenuItem(self.menu_handler, "Toggle", 1, 1)

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def XPluginDisable(self):
        if self.isLogging[0]:
            self.StopLogging()

    def XPluginStop(self):
        pass

    def StartLogging(self):
        time = datetime.datetime.now().strftime('%H:%M:%S')
        date = datetime.datetime.now().strftime('%d/%m/%Y')
        log_path = os.path.join(
            'G:\\SteamLibrary\\steamapps\\common\\X-Plane 12\\Output\\fdr_files',
            f"FDR_Log_{date + "_" + time}.fdr"
        )
        self.file[0] = open(log_path, 'w')

        self.file[0].write("A\n")
        self.file[0].write("3\n\n")

        self.file[0].write("ACFT, Aircraft/Laminar Research/Airbus A330-300/A330.acf\n")
        self.file[0].write("TAIL, N12345\n")
        self.file[0].write(f"TIME, {time}\n")
        self.file[0].write(f"DATE, {date}\n")
        self.file[0].write("PRES, 29.92\n")
        self.file[0].write("DISA, 0\n")
        self.file[0].write("WIND, 180,10\n\n")
    
        for name, ref in self.datarefs.items():
            if name not in ['latitude', 'longitude', 'press_altitude', 'mag_heading', 'pitch', 'roll']:
                self.file[0].write(f"DREF, {ref}\t\t\t1.0\n\n")

            self.file[0].write("COMM,Sample,Long,Lat,PressureAlt,MagHeading,Pitch,Roll,BaroAlt,VSPD,SLAT,FLAP,LDG\n")
            self.counter[0] = 0
            xp.registerFlightLoopCallback(self.FlightLoopCallback, self.sampling_rate, 0)
            xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window)
            self.isLogging[0] = self.isDrawing[0] = True
            xp.log("Logging --> Started.")

    def StopLogging(self):
        if self.file[0]:
            self.file[0].close()
            self.file[0] = None
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback)
        if self.isDrawing[0]:
            xp.unregisterDrawCallback(self.DrawCallback, 0)
        self.isLogging[0] = self.isDrawing[0] = False
        xp.log("Logging --> Stopped.")

    def ToggleLogging(self):
        if self.isLogging[0]:
            self.StopLogging()
        else:
            self.StartLogging()

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        i = self.counter[0]
        values = [i] + [
            xp.getDataf(self.datarefs_pointers[param]) if self.datarefs_pointers.get(param) else float('nan')
            for param in self.parameters
        ]
        self.file[0].write("DATA," + ",".join(f"{val:.5f}" for val in values) + "\n")
        self.file[0].flush()
        self.counter[0] += 1

        return 1

    def DrawCallback(self, inPhase, inIsBefore, inRefCon):
        if self.isLogging[0]:
            screen_width, screen_height = xp.getScreenSize()
            xp.drawString(
                rgb=(1.0, 1.0, 1.0),
                x=screen_width + 5 - screen_width,
                y=screen_height + 5 - screen_height,
                value=f"[LOGGING TIMESERIES DATA] | Samples: {self.counter[0]:,}",
                fontID=1
            )
        return 1