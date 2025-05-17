from XPPython3 import xp  # type: ignore
import os
import datetime

datarefs = {
    'latitude': 'sim/flightmodel/position/latitude',
    'longitude': 'sim/flightmodel/position/longitude',
    'press_altitude': 'sim/flightmodel2/position/pressure_altitude',
    'baro_altitude': 'sim/cockpit2/gauges/indicators/altitude_ft_pilot',
    'mag_heading': 'sim/flightmodel/position/mag_psi',
    'pitch': 'sim/flightmodel/position/theta',
    'roll': 'sim/flightmodel/position/phi',
    'qnh': 'sim/cockpit/misc/barometer_setting',
    'cas': 'sim/cockpit2/gauges/indicators/airspeed_kts_pilot',
    'tas': 'sim/cockpit2/gauges/indicators/true_airspeed_kts_pilot',
    'gs': 'sim/cockpit2/gauges/indicators/ground_speed_kt',
    'vspd': 'sim/cockpit2/gauges/indicators/vvi_fpm_pilot',
    'oat': 'sim/cockpit2/temperature/outside_air_temp_degc',
    'flap': 'sim/flightmodel/controls/flaprat',
    'slat': 'sim/flightmodel/controls/slatrat',
    'gear_down': 'laminar/A333/fws/landing_gear_down'
}

isLogging = [False]
isDrawing = [False]
sampling_rate = 1
counter = [0]
file = [None]

def draw_callback(inPhase, inIsBefore, inRefcon):
    if isLogging[0]:
        screen_width, screen_height = xp.getScreenSize()
        xp.drawString(
            rgb=(1.0, 1.0, 1.0),
            x=screen_width + 5 - screen_width,
            y=screen_height + 5 - screen_height,
            value=f"[LOGGING TIMESERIES] | Samples: {counter[0]:,}",
            fontID=1
        )
    return 1

def start_logging():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join('G:\\SteamLibrary\\steamapps\\common\\X-Plane 12\\Output\\fdr_files', f"FDR_Log_{timestamp}.fdr")
    file[0] = open(log_path, "w")

    file[0].write("A\n")
    file[0].write("3\n\n")

    file[0].write("ACFT, Aircraft/Laminar Research/Airbus A330-300/A330.acf\n")
    file[0].write("TAIL, N12345\n")
    file[0].write(f"TIME, {datetime.datetime.now().strftime('%H:%M:%S')}\n")
    file[0].write(f"DATE, {datetime.datetime.now().strftime('%d/%m/%Y')}\n")
    file[0].write("PRES, 30.01\n")
    file[0].write("DISA, 0\n")
    file[0].write("WIND, 180,10\n\n")

    for name, ref in datarefs.items():
        if name not in ['longitude', 'latitude', 'press_altitude', 'mag_heading', 'pitch', 'roll']:
            file[0].write(f"DREF, {ref}\t\t\t1.0\n")

    file[0].write("COMM,Sample,Long,Lat,PressureAlt,MagHeading,Pitch,Roll,BaroSet,CAS,TAS,GS,BaroAlt,VSPD,OAT,SLAT,FLAP,LDG\n")
    counter[0] = 0
    xp.registerFlightLoopCallback(flight_loop_callback, sampling_rate, 0)
    xp.registerDrawCallback(draw_callback, xp.Phase_Window)
    isLogging[0] = isDrawing[0] = True
    xp.log("Logging --> Started.")

def stop_logging():
    if file[0]:
        file[0].close()
        file[0] = None
    xp.unregisterFlightLoopCallback(flight_loop_callback, 0)
    if isDrawing[0]:
        xp.unregisterDrawCallback(draw_callback, 0)
        isDrawing[0] = False
    isLogging[0] = False
    xp.log("Logging --> Stopped.")

def toggle_logging(inMenuRef, inItemRef):
    if isLogging[0]:
        stop_logging()
    else:
        start_logging()

def flight_loop_callback(elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
    global counter, file
    i = counter[0]
    values = [i] + [xp.getDataf(xp.findDataRef(datarefs[param])) for param in [
        "longitude", "latitude", "press_altitude", "mag_heading", "pitch", "roll",
        "qnh", "cas", "tas", "gs", "baro_altitude", "vspd", "oat", "slat", "flap", "gear_down"
    ]]
    file[0].write("DATA," + ",".join(f"{val:.10f}" for val in values) + "\n")
    file[0].flush()
    counter[0] += 1

    return 1

class PythonInterface:

    def XPluginStart(self):
        name = "Generate FDR Files"
        signature = "aryanshukla.plugin002.generatefdr"
        description = "Logs Timeseries Data Into A FDR File"

        menu_id = xp.createMenu("genFDR", None, 0, toggle_logging, 0)
        xp.appendMenuItem(menu_id, "Toggle", 1, 1)

        return name, signature, description

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        if isLogging[0]:
            stop_logging()

    def XPluginStop(self):
        if isLogging[0]:
            stop_logging()