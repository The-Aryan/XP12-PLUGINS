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
        self.Name = "Plot Timeseries Data Live"
        self.Sig = "aryanshukla.plugin003.paraviz"
        self.Desc = "Plots Timeseries Data Live"

        self.datarefs = {
            'alt': 'sim/flightmodel2/position/pressure_altitude',
        }

        self.max_points = 1000
        self.time_history = deque(maxlen=self.max_points)
        self.alt_history = deque(maxlen=self.max_points)
        self._lock = threading.Lock()

        self._running = False
        self._plot_thread = None
        self._app = None

        self.start_time = None

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        if not self._running:
            return 0.1
        
        self.parameters_ts = {
            param: xp.getDataf(self.datarefs_pointers[param])
            for param in list(self.datarefs_pointers.keys())
        }

        with self._lock:
            self.time_history.append(time.time() - self.start_time)
            self.alt_history.append(self.parameters_ts['alt'])

        return 0.1

    def XPluginStart(self):
        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in list(self.datarefs.keys())
        }
        self.start_time = time.time()
        self._running = True
        self._plot_thread = threading.Thread(target=self._start_plot, daemon=True)
        self._plot_thread.start()

        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.1, 0)
        xp.log("ParaViz --> Started.")

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self):
        return 1
    
    def XPluginDisable(self):
        self._running = False
        
    def XPluginReceiveMessage(self, inMessage, inParam1, inParam2):
        pass

    def XPluginStop(self):
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
        self._running = False

        try:
            if self._app:
                QtCore.Qtimer.singleShot(0, self._app.quit)
        except Exception:
            pass

        xp.log("ParaViz --> Stopped.")

    def _start_plot(self):
        self._app = QtWidgets.QApplication(sys.argv)
        win = pg.GraphicsLayoutWidget(show=True, title="Live Timeseries Data")
        win.resize(600, 900)

        alt_plot = win.addPlot(title="ALTITUDE (ft)")
        alt_plot.showGrid(x=True, y=True)
        alt_plot.setLabel('left', 'Altitude (ft)', units='ft')
        alt_plot.setLabel('bottom', 'Time (s)', units='s')
        alt_curve = alt_plot.plot(pen=pg.mkPen(width=2))

        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: self._update_plot(alt_curve))
        timer.start(100)

        self._app.exec_()

    def _update_plot(self, alt_curve):
        with self._lock:
            t = list(self.time_history)
            alt = list(self.alt_history)

        if not t:
            return
        
        alt_curve.setData(t, alt)
        alt_curve.curve.setAutoVisible(True)