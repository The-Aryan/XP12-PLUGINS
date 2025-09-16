"""
Author:         Aryan Shukla
Plugin Name:    Plot Timeseries Data Live (ParaViz)
Tools Used:     Python 3.13.3, XPPython3 4.5.0
"""

import time
import threading
from queue import Queue, Empty
from collections import deque
from XPPython3 import xp  # type: ignore
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


class PlotterWindow(QtWidgets.QWidget):
    def __init__(self, dataQ, paraNames, notifyStop):
        super().__init__()

        self.dataQ = dataQ
        self.paraNames = paraNames
        self.notifyStop = notifyStop

        self.isRunning = True
        self.isPaused = False
        self.isClosing = False

        self.maxlen = 14400
        self.data = {param: deque(maxlen=self.maxlen) for param in self.paraNames}
        self.time = deque(maxlen=self.maxlen)

        self.setStyleSheet("""
            QWidget {
                background-color: #0f1116;
                color: #e0e0e0;
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 12pt;
            }
            QCheckBox {
                spacing: 8px;
                font-weight: 600;
            }
            QPushButton {
                background-color: #2d89ef;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 12pt; font-weight: 600; color: white;
            }
            QPushButton:hover {
                background-color: #1b5fbf;
            }
        """)

        main_layout = QtWidgets.QHBoxLayout(self)

        self.plot_widget = pg.PlotWidget(background="#0f1116")
        pi = self.plot_widget.getPlotItem()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        pi.getAxis("bottom").setTextPen("#CCCCCC")
        pi.getAxis("left").setTextPen("#CCCCCC")
        pi.showAxis("right", False)

        main_layout.addWidget(self.plot_widget, 4)

        self.base_curve = self.plot_widget.plot([], [], pen=pg.mkPen((0, 0, 0, 0)))
        self.curves = {}
        self.viewboxes = {}
        self.axes = {}

        colors = ["#4DB6AC", "#F08913", "#DDC8E0", "#FFD54F", "#90A4AE", "#2B16E9"]

        side_panel = QtWidgets.QFrame()
        side_panel.setStyleSheet("QFrame { background-color: #181b22; border-radius: 12px; }")
        side_layout = QtWidgets.QVBoxLayout(side_panel)
        side_layout.setContentsMargins(15, 15, 15, 15)

        title = QtWidgets.QLabel("<--- PARAMETERS --->")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #ffffff;")
        side_layout.addWidget(title)

        self.checkboxes = {}

        for i, param in enumerate(self.paraNames):
            color = colors[i % len(colors)]

            vb = pg.ViewBox()
            axis = pg.AxisItem(orientation="right")
            axis.setPen(color)
            axis.setTextPen(color)
            axis.setLabel(text=param, color=color)

            pi.layout.addItem(axis, 2, 3 + i)
            pi.scene().addItem(vb)
            axis.linkToView(vb)
            vb.setXLink(pi.vb)

            curve = pg.PlotCurveItem(pen=pg.mkPen(color, width=2))
            vb.addItem(curve)

            self.curves[param] = curve
            self.viewboxes[param] = vb
            self.axes[param] = axis

            axis.setVisible(False)
            curve.setVisible(False)

            cb = QtWidgets.QCheckBox(param)
            cb.setStyleSheet(f"QCheckBox {{ color: {color}; font-weight: bold; }}")
            cb.stateChanged.connect(self.UpdateSelected)
            side_layout.addWidget(cb)
            self.checkboxes[param] = cb

        side_layout.addStretch()

        btn_row = QtWidgets.QGridLayout()
        self.pause_btn = QtWidgets.QPushButton("Pause")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        btn_row.addWidget(self.pause_btn, 0, 0, 1, 2)
        btn_row.addWidget(self.reset_btn, 1, 0, 1, 2)
        side_layout.addLayout(btn_row)
        self.pause_btn.clicked.connect(self.TogglePauseResume)
        self.reset_btn.clicked.connect(self.ResetPlotting)

        main_layout.addWidget(side_panel, 1)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.UpdatePlot)
        self.t0 = time.time()
        self.timer.start(200)

        pi.vb.sigResized.connect(self.UpdateViews)
        self.UpdateViews()

        first_param = self.paraNames[0]
        self.checkboxes[first_param].setChecked(True)
        self.UpdateSelected()

    def closeEvent(self, event):
        self.isClosing = True
        if self.timer.isActive():
            self.timer.stop()
        try:
            self.notifyStop()
        finally:
            super().closeEvent(event)

    def UpdateViews(self):
        pi = self.plot_widget.getPlotItem()
        vb_main = pi.vb
        rect = vb_main.sceneBoundingRect()
        for vb in self.viewboxes.values():
            vb.setGeometry(rect)
            vb.linkedViewChanged(vb_main, vb.XAxis)

    def UpdateSelected(self):
        for p, cb in self.checkboxes.items():
            vis = cb.isChecked()
            self.curves[p].setVisible(vis)
            self.axes[p].setVisible(vis)
        self.UpdateViews()

    def TogglePauseResume(self):
        if not self.isRunning:
            return
        if not self.isPaused:
            self.isPaused = True
            self.timer.stop()
            self.pause_btn.setText("Resume")
        else:
            self.isPaused = False
            self.timer.start(200)
            self.pause_btn.setText("Pause")

    def ResetPlotting(self):
        self.isRunning = True
        self.isPaused = False
        if self.timer.isActive():
            self.timer.stop()
        self.time.clear()
        for p in self.paraNames:
            self.data[p].clear()
            self.curves[p].setData([], [])
        self.base_curve.setData([], [])
        self.pause_btn.setText("Pause")

        self.t0 = time.time()
        for cb in self.checkboxes.values():
            cb.setChecked(False)
        first_param = self.paraNames[0]
        self.checkboxes[first_param].setChecked(True)
        self.UpdateSelected()
        self.timer.start(200)

    def UpdatePlot(self):
        if not self.isRunning or self.isPaused or self.isClosing:
            return

        latest = None
        try:
            while True:
                latest = self.dataQ.get_nowait()
        except Empty:
            pass

        if latest is None:
            return

        timestamp, values = latest
        self.time.append(timestamp - self.t0)
        for p, v in values.items():
            self.data[p].append(v)

        if len(self.time) > 0:
            th = list(self.time)
            self.base_curve.setData(th, [0] * len(th))

            for p, cb in self.checkboxes.items():
                if cb.isChecked() and len(self.data[p]) > 0:
                    self.curves[p].setData(th, list(self.data[p]))
                    self.viewboxes[p].enableAutoRange(axis=self.viewboxes[p].YAxis, enable=True)

        self.UpdateViews()


class PythonInterface:
    def __init__(self):
        self.Name = "ParaViz"
        self.Sig = "plugin003.paraviz.byaryanshukla"
        self.Desc = "Plots Timeseries Data in Real-Time"

        self.parameters = {
            "ALT": "sim/flightmodel2/position/pressure_altitude",
            "CAS": "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
            'PTCH': 'sim/flightmodel/position/theta',
            'ROLL': 'sim/flightmodel/position/phi',
            'VSPD': 'sim/cockpit2/gauges/indicators/vvi_fpm_pilot'
        }
        self.datarefs_pointer = {}

        self.isPlotting = False
        self.qtThread = None
        self.qtApp = None
        self.dataQ = Queue()
        self.window = None
        self.stopRequested = threading.Event()

    def XPluginStart(self):
        self.paravizMenuId = xp.createMenu("ParaViz", None, 0, self.MenuHandler, None)
        self.toggleMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Toggle: ON", 'toggle')

        self.datarefs_pointer = {param: xp.findDataRef(dataref) for param, dataref in self.parameters.items()}

        return self.Name, self.Sig, self.Desc

    def XPluginEnable(self): return 1
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam): pass
    def XPluginDisable(self): pass
    def XPluginStop(self): pass

    def MenuHandler(self, menuRef, itemRef):
        self.isPlotting = not self.isPlotting
        if self.isPlotting:
            xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: OFF")
            self.StartPlotting()
        else:
            xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: ON")
            self.StopPlotting()

    def StartPlotting(self):
        self.qtThread = threading.Thread(
            target=self.LaunchUI,
            name="ParaVizQtThread",
            daemon=True
        )
        self.qtThread.start()
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1, None)
        xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

    def LaunchUI(self):
        self.qtApp = QtWidgets.QApplication([])
        self.window = PlotterWindow(
            self.dataQ,
            list(self.parameters.keys()),
            notifyStop=self.RequestStop
        )
        self.window.setWindowTitle("ParaViz")
        self.window.show()

        self.qtApp.setQuitOnLastWindowClosed(True)
        try:
            self.qtApp.exec_()
        finally:
            self.window = None
            self.qtApp = None

    def RequestStop(self):
        self.stopRequested.set()

    def StopPlotting(self):
        self.stopRequested.clear()

        try:
            xp.unregisterFlightLoopCallback(self.FlightLoopCallback, None)
        except Exception:
            pass
        try:
            xp.unregisterDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)
        except Exception:
            pass

        if self.window is not None:
            try:
                QtCore.QMetaObject.invokeMethod(
                    self.window, "close", QtCore.Qt.QueuedConnection
                )
            except Exception:
                try:
                    self.window.close()
                except Exception:
                    pass

        if self.qtThread is not None and self.qtThread.is_alive():
            self.qtThread.join(timeout=2.0)
        self.qtThread = None

        if self.isPlotting:
            self.isPlotting = False
            try:
                xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: ON")
            except Exception:
                pass

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        if self.stopRequested.is_set():
            self.StopPlotting()
            return 0

        values = {p: xp.getDataf(dref) for p, dref in self.datarefs_pointer.items()}
        self.dataQ.put((time.time(), values))
        return 1

    def DrawCallback(self, inPhase, inAfter, inRefCon):
        try:
            screen_width, screen_height = xp.getScreenSize()
            xp.drawString(
                rgb=(1.0, 0.0, 0.0),
                x=screen_width - 200,
                y=screen_height - 20,
                value="PLOTTING TIMESERIES DATA ...",
                fontID=xp.Font_Proportional
            )
        except Exception:
            pass
        return 1