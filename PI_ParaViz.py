'''
Author:         Aryan Shukla
Plugin Name:    Plot Timeseries Data Live
Tools Used:     Python 3.13.3, XPPython3 4.5.0
'''

import time
import sys
import threading
from collections import deque
from XPPython3 import xp  # type: ignore
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class PythonInterface:
    def __init__(self):
        self.Name = "ParaViz"
        self.Sig = "plugin003.paraviz.byaryanshukla"
        self.Desc = "Plots Timeseries Data in Real-Time"

        self.parameters = {
            "alt": {
                "enabled": True,
                "dref": "sim/flightmodel2/position/pressure_altitude",
                "ref": None,
                "menuItemId": None,
                "timeseries": deque(maxlen=7200)
            },
            "cas": {
                "enabled": False,
                "dref": "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
                "ref": None,
                "menuItemId": None,
                "timeseries": deque(maxlen=7200)
            },
        }

        self.isPlotting = False
        self.tStart = None

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self.app = None
        self.win = None
        self.curves = {}
        self.plotWidget = None
        self.qtTimer = None
        self.qtThread = None

    def XPluginStart(self):
        self.paravizMenuId = xp.createMenu(
            "ParaViz",
            None,
            0,
            self.MenuHandler,
            None
        )
        self.toggleMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Toggle: ON", 'toggle')
        self.paramsMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Parameters", None)
        self.paramsMenuId = xp.createMenu(
            "Parameters",
            self.paravizMenuId,
            self.paramsMenuItemId,
            self.MenuHandler,
            None
        )

        for pname, cfg in self.parameters.items():
            cfg["menuItemId"] = xp.appendMenuItem(
                self.paramsMenuId,
                (
                    f"{pname.upper()} - Hide" if cfg["enabled"]
                    else f"{pname.upper()} - Show"
                ),
                pname
            )
            cfg["ref"] = xp.findDataRef(cfg["dref"])

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self):
        return 1
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
    
    def XPluginDisable(self):
        if self.isPlotting:
            self.StopPlotting()
            return None

    def XPluginStop(self):
        try:
            self._shutdown_qt()  # variable does not exist
        except Exception as e:
            xp.log(f"ParaViz: Error On Shutdown: {e}")

    def MenuHandler(self, menuRef, itemRef):
        if itemRef == 'toggle':
            self.isPlotting = not self.isPlotting
            if self.isPlotting:
                xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: OFF")
                self.StartPlotting()
            else:
                xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: ON")
                self.StopPlotting()

        elif itemRef in self.parameters:
            cfg = self.parameters[itemRef]
            cfg["enabled"] = not cfg["enabled"]
            xp.setMenuItemName(
                self.paramsMenuId,
                cfg["menuItemId"],
                (
                    f"{itemRef.upper()} - Hide" if self.parameters[itemRef]["enabled"]
                    else f"{itemRef.upper()} - Show"
                )
            )

    def StartPlotting(self):

        if self.qtThread is None or not self.qtThread.is_alive():
            self._stop_event.clear()
            self.qtThread = threading.Thread(target=self._run_qt, name="ParaVizQtThread", daemon=True)
            self.qtThread.start()
        else:
            if self.win:
                self.win.show()

        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1, None)
        xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

    def StopPlotting(self):
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, None)
        xp.unregisterDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

        if self.win:
            self.win.hide()

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        if self.tStart is None:
            self.tStart = time.time()

        t = time.time() - self.tStart

        with self._lock:
            for pname, cfg in self.parameters.items():
                if cfg["enabled"]:
                    val = xp.getDataf(cfg["ref"])
                    cfg["timeseries"].append((t, val))

        return 1
    
    def DrawCallback(self, inPhase, inAfter, inRefCon):
        screen_width, screen_height = xp.getScreenSize()
        xp.drawString(
            rgb=(1.0, 0.0, 0.0),
            x=screen_width - 250,
            y=screen_height + 5 - screen_height,
            value=f"PLOTTING TIMESERIES DATA ...",
            fontID=xp.Font_Proportional
        )
        return 1
    
    def _run_qt(self):

            self.app = QtWidgets.QApplication(["ParaViz"])
            self.win = QtWidgets.QMainWindow()
            self.win.setWindowTitle("ParaViz — Live Plot")
            self.win.resize(900, 560)

            self.plotWidget = pg.PlotWidget(title="ParaViz Timeseries")
            self.plotWidget.showGrid(x=True, y=True)
            self.plotWidget.setDownsampling(auto=True)
            self.plotWidget.setClipToView(True)
            self.plotWidget.addLegend()
            self.win.setCentralWidget(self.plotWidget)

            self.curves = {}
            for pname, cfg in self.parameters.items():
                if cfg["enabled"]:
                    self.curves[pname] = self.plotWidget.plot(
                        pen=pg.mkPen(color='y', width=2), name=pname.upper()
                    )

            self.qtTimer = QtCore.QTimer()
            self.qtTimer.timeout.connect(self._update_qt)
            self.qtTimer.start(1200)

            self.win.show()
            self.app.exec_()

            self._qt_timer = None
            self.curves.clear()
            self.plotWidget = None
            self.win = None
            self.app = None

    def _update_qt(self):
        with self._lock:
            snapshot = {
            pname: list(cfg["timeseries"]) if cfg["enabled"] else []
            for pname, cfg in self.parameters.items()
            }
        for pname, series in snapshot.items():
            if pname in self.curves:
                if series:
                    xs, ys = zip(*series)
                    self.curves[pname].setData(xs, ys)
                else:
                    self.curves[pname].clear()

    def _shutdown_qt(self):
        if self.app is not None:
            if self._qt_timer is not None:
                self._qt_timer.stop()
            if self.win is not None:
                self.win.close()
            self.app.quit()

        if self.qtThread is not None and self.qtThread.is_alive():
            self.qtThread.join(timeout=1.0)
        self.qtThread = None
