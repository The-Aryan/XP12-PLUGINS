from XPPython3 import xp # type: ignore

menu_id = altitude_ref = ias_ref = None

def add_menu():
    menu_id = xp.createMenu("FOVA", xp.findPluginsMenu(), 0, menu_handler, 0)
    xp.appendMenuItem(menu_id, "Log Flight Data", 1)

def menu_handler(menuRef, itemRef):
    if itemRef == 1:
        log_flight_data()

def log_flight_data():
    altitude = xp.getDataf(altitude_ref)
    ias = xp.getDataf(ias_ref)
    print(f"Altitude: {altitude}, IAS: {ias}")

class PythonInterface:
    def XPluginStart(self):
        global menu_id, altitude_ref, ias_ref
        name = "FOVA"
        signature = "aryanshukla.plugin003.fova"
        description = "Displays FOVA Data"
        
        menu_id = xp.createMenu("FOVA", None, 0, None, 0)
        xp.appendMenuItem(menu_id, "Toggle", 1, 1)
        
        altitude_ref = xp.findDataRef("'sim/flightmodel2/position/pressure_altitude'")
        ias_ref = xp.findDataRef("sim/cockpit2/gauges/indicators/airspeed_kts_pilot")
        
        return name, signature, description