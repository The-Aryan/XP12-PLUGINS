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
            },
            "cas": {
                "enabled": False,
                "dref": "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
            },
        }

        self.isPlotting = False
        self.threadLock = threading.Lock()
        self.startTime = 0.0

        self.datarefs = {}
        self.timeTS = deque(maxlen=self.max_points)
        self.paramTS = {p: deque(maxlen=self.max_points) for p in self.parameters}

        self.plotThread = None

    def XPluginStart(self):
        self.paravizMenuId = xp.createMenu(
            "ParaViz",          # name
            None,               # parentMenuID
            0,                  # parentItem
            self.ToggleLogging, # handler
            None                # refCon
        )
        self.toggleMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Toggle: ON", 1)
        self.paramsMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Parameters", 2)
        self.paramsMenuId = xp.createMenu(
            "Parameters",
            self.paravizMenuId,
            self.paramsMenuItemId,
            self.TogglePlotting,
            0
        )
        for i, pname in enumerate(self.parameters.keys()):
            self.param_items[pname] = xp.appendMenuItem(
                self.paramsMenuId,
                (f"{pname.upper()} - Hide" if self.parameters[pname]["enabled"] else f"{pname.upper()} - Show"),
                None
            )

        return self.Name, self.Sig, self.Desc
    
    def XPluginEnable(self):
        return 1
    
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
    
    def XPluginDisable(self):
        pass

    def XPluginStop(self):
        xp.log("Parameter Visualization: Stopped")

    def TogglePlotting(self, menuRef, itemRef):
        if itemRef == 1:
            if self.isPlotting:
                self.StopPlotting()
            else:
                self.StartPlotting()

    # def param_menu_handler(self, menuRef, itemRef):
    #     pname = list(self.parameters.keys())[itemRef]
    #     self.parameters[pname]["enabled"] = not self.parameters[pname]["enabled"]

    #     xp.setMenuItemName(
    #         self.params_menu,
    #         self.param_items[pname],
    #         ("X" if self.parameters[pname]["enabled"] else "") + pname
    #     )

    #     if self.isPlotting:
    #         self._request_ui_rebuild()

    def StartPlotting(self):
        self.datarefs = {p: xp.findDataRef(cfg["dref"]) for p, cfg in self.parameters.keys()}
        with self.threadLock:
            self.startTime = time.time()
            self.timeTS.clear()
            for p in self.parameters:
                self.paramTS[p].clear()

        self.isPlotting = True
        self.plotThread = threading.Thread(target=self._ui_thread, daemon=True)
        self.plotThread.start()

        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1.0, 0)
        xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: OFF")
        xp.log("Parameter Visualization: Started")

    def StopPlotting(self):
        if not self.isPlotting:
            return
        self.isPlotting = False
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)

        if self._app:
            QtCore.QTimer.singleShot(0, self._app.quit)
        xp.setMenuItemName(self.menu, self.toggle_item, "Toggle: ON")

    # def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
    #     if not self.isPlotting:
    #         return 0.0
        
    #     t = time.time() - self.start_time

    #     with self.threadLock:
    #         self.time_history.append(t)
    #         for pname, cfg in self.parameters.items():
    #             if not self.datarefs.get(pname):
    #                 continue
    #             try:
    #                 raw = xp.getDataf(self.datarefs[pname])
    #             except Exception:
    #                 continue

    #             self.buffers[pname].append(raw)

    #     return 1.0
    
    # def _ui_thread(self):
    #     self._app = QtWidgets.QApplication(sys.argv)
    #     self._build_window()

    #     self.timer = QtCore.QTimer()
    #     self.timer.setTimerType(QtCore.Qt.PreciseTimer)
    #     self.timer.timeout.connect(self._update_plot)
    #     self.timer.start(self.timer_ms)

    #     self._app.exec_()
    #     self._app = None
    #     self.timer = None
    #     self.win = None
    #     self.plot = None
    #     self.right_vb = None
    #     self.curves.clear()
    #     self._plotted_pair = tuple()

    # def _build_window(self):
    #     self.win = pg.GraphicsLayoutWidget(show=True, title="Live Data Plotter")
    #     self.win.resize(980, 580)

    #     self.plot = self.win.addPlot(title="Parameters vs Time")
    #     self.plot.showGrid(x=True, y=True)
    #     self.plot.setLabel('bottom', 'Time', units='s')

    #     left_param, right_param = self._pick_enabled_pair()

    #     if left_param:
    #         self.plot.setLabel('left', left_param.split(' (')[0], units=self._units_from_name(left_param))
    #         self.curves[left_param] = self.plot.plot(pen=pg.mkPen(width=2))
    #     else:
    #         self.plot.setLabel('left', '')

    #     self.right_vb = None
    #     if right_param:
    #         self.plot.showAxis('right')
    #         self.plot.setLabel('right', right_param.split(' (')[0], units=self._units_from_name(right_param))
    #         self.plot.getAxis('right').setPen(pg.mkPen(width=1))
    #         self.right_vb = pg.ViewBox()
    #         self.plot.scene().addItem(self.right_vb)
    #         self.plot.getAxis('right').linkToView(self.right_vb)
    #         self.right_vb.setXLink(self.plot)
    #         def _sync():
    #             self.right_vb.setGeometry(self.plot.vb.sceneBoundingRect())
    #             self.right_vb.linkedViewChanged(self.plot.vb, self.right_vb.XAxis)
    #         _sync()
    #         self.plot.vb.sigResized.connect(_sync)

    #         c = pg.PlotCurveItem(pen=pg.mkPen(width=2))
    #         self.right_vb.addItem(c)
    #         self.curves[right_param] = c
    #     else:
    #         self.plot.hideAxis('right')

    #     self._plotted_pair = (left_param, right_param)

    # def _request_ui_rebuild(self):
    #     self._plotted_pair = tuple()

    # def _update_plot(self):
    #     left_param, right_param = self._pick_enabled_pair()
    #     if (left_param, right_param) != self._plotted_pair:
    #         self.win.close() if self.win else None
    #         self.curves.clear()
    #         self._build_window()

    #     with self.threadLock:
    #         t = list(self.time_history)
    #         left_data  = list(self.buffers.get(left_param, []))  if left_param  else None
    #         right_data = list(self.buffers.get(right_param, [])) if right_param else None

    #     if not t:
    #         return

    #     if left_param and left_param in self.curves:
    #         self.curves[left_param].setData(t, left_data)
    #     if right_param and right_param in self.curves:
    #         self.curves[right_param].setData(t, right_data)

    # def _pick_enabled_pair(self):
    #     """Return up to two enabled parameter names (left, right)."""
    #     enabled = [p for p, cfg in self.parameters.items() if cfg["enabled"]]
    #     if not enabled:
    #         return (None, None)
    #     if len(enabled) == 1:
    #         return (enabled[0], None)
    #     return (enabled[0], enabled[1])

    # @staticmethod
    # def _units_from_name(pname):
    #     if '(' in pname and ')' in pname:
    #         return pname[pname.find('(')+1:pname.find(')')]
    #     return ""

    
