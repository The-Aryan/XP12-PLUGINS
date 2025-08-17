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
                "timeseries": []
            },
            "cas": {
                "enabled": False,
                "dref": "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
                "ref": None,
                "menuItemId": None,
                "timeseries": []
            },
        }

        self.isPlotting = False
        self.paramMenuItems = {}

        self.tStart = None

        self.app = None
        self.win = None
        self.curves = {}
        self.plotWidget = None

        self.qtThread = None

    def XPluginStart(self):
        self.paravizMenuId = xp.createMenu(
            "ParaViz",          # name
            None,               # parentMenuID
            0,                  # parentItem
            self.MenuHandler,   # handler
            None                # refCon
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
        pass

    def XPluginStop(self):
        xp.log("XPluginStop")

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

        def _run_qt():
            self.app = QtWidgets.QApplication(sys.argv)
            self.win = QtWidgets.QMainWindow()
            self.plotWidget = pg.PlotWidget(title="ParaViz")
            self.win.setCentralWidget(self.plotWidget)
            self.win.resize(800, 500)
            self.win.show()
            self.app.exec_()

        self.qtThread = threading.Thread(target=_run_qt, daemon=True)
        self.qtThread.start()

        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1, None)

    def StopPlotting(self):
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, None)

        if self.app:
            self.app.quit()
            self.app = None
        self.win = None
        self.plotWidget = None

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        if self.tStart is None:
            self.tStart = time.time()

        t = time.time() - self.tStart

        for pname, cfg in self.parameters.items():
            if cfg["enabled"]:
                val = xp.getDataf(cfg["ref"])
                cfg["timeseries"].append((t, val))

                xp.log(f"[ParaViz] t={t:.1f} {pname.upper()}={val:.1f}")

        return 1
    
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

    
