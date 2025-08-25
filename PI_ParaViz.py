"""
Author:         Aryan Shukla
Plugin Name:    Plot Timeseries Data Live (ParaViz)
Tools Used:     Python 3.13.3, XPPython3 4.5.0
"""

import time
import sys
import threading
from queue import Queue, Empty
from collections import deque
from XPPython3 import xp  # type: ignore
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


# =========================
#        Plot Window
# =========================
class PlotterWindow(QtWidgets.QWidget):
    # 🟢 CHANGE: pass a thread-safe notifier (no xp.* in GUI thread)
    def __init__(self, data_queue, parameters, notify_stop, history_seconds=60):
        super().__init__()

        self.data_queue = data_queue
        self.parameters = parameters
        self.notify_stop = notify_stop  # -> sets an Event only (no sim API here)

        self.isRunning = True
        self.isPaused = False
        self._isClosing = False  # 🟢 CHANGE: guard to stop updates during teardown

        # 🟢 CHANGE: bounded history with deque to prevent RAM bloat
        self.maxlen = max(10, int(history_seconds * 10))  # assume 10 Hz
        self.data = {p: deque(maxlen=self.maxlen) for p in self.parameters}
        self.time_history = deque(maxlen=self.maxlen)

        # --- Styling ---
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1116;
                color: #e0e0e0;
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 11pt;
            }
            QCheckBox { spacing: 8px; font-weight: 600; }
            QPushButton {
                background-color: #2d89ef;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 10pt; font-weight: 600; color: white;
            }
            QPushButton:hover { background-color: #1b5fbf; }
        """)

        main_layout = QtWidgets.QHBoxLayout(self)

        # --- Plot Widget ---
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

        colors = ["#4DB6AC", "#64B5F6", "#BA68C8", "#FFD54F", "#90A4AE", "#81C784"]

        # --- Side Panel ---
        side_panel = QtWidgets.QFrame()
        side_panel.setStyleSheet("QFrame { background-color: #181b22; border-radius: 12px; }")
        side_layout = QtWidgets.QVBoxLayout(side_panel)
        side_layout.setContentsMargins(15, 15, 15, 15)

        title = QtWidgets.QLabel("Parameters")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #ffffff;")
        side_layout.addWidget(title)

        self.checkboxes = {}

        for i, param in enumerate(self.parameters):
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
            cb.stateChanged.connect(self.update_selected)
            side_layout.addWidget(cb)
            self.checkboxes[param] = cb

        side_layout.addStretch()

        # --- Buttons Row ---
        btn_row = QtWidgets.QGridLayout()
        self.pause_btn = QtWidgets.QPushButton("⏸ Pause")
        self.reset_btn = QtWidgets.QPushButton("🔄 Reset")
        btn_row.addWidget(self.pause_btn, 0, 0, 1, 2)
        btn_row.addWidget(self.reset_btn, 1, 0, 1, 2)
        side_layout.addLayout(btn_row)
        self.pause_btn.clicked.connect(self.toggle_pause_resume)
        self.reset_btn.clicked.connect(self.reset_plotting)

        main_layout.addWidget(side_panel, 1)

        # --- Timer ---
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.t0 = time.time()
        self.timer.start(200)  # 5 Hz GUI refresh

        pi.vb.sigResized.connect(self.update_views)
        self.update_views()

        # Auto-enable first parameter
        first_param = self.parameters[0]
        self.checkboxes[first_param].setChecked(True)
        self.update_selected()

    # 🟢 CHANGE: Never touch X-Plane here. Only stop timer, flag closing, and notify plugin thread.
    def closeEvent(self, event):
        self._isClosing = True
        if self.timer.isActive():
            self.timer.stop()
        try:
            self.notify_stop()   # sets an Event; plugin thread will do xp.* safely
        finally:
            super().closeEvent(event)

    # --- Geometry sync ---
    def update_views(self):
        pi = self.plot_widget.getPlotItem()
        vb_main = pi.vb
        rect = vb_main.sceneBoundingRect()
        for vb in self.viewboxes.values():
            vb.setGeometry(rect)
            vb.linkedViewChanged(vb_main, vb.XAxis)

    def update_selected(self):
        for p, cb in self.checkboxes.items():
            vis = cb.isChecked()
            self.curves[p].setVisible(vis)
            self.axes[p].setVisible(vis)
        self.update_views()

    # --- Controls ---
    def toggle_pause_resume(self):
        if not self.isRunning:
            return
        if not self.isPaused:
            self.isPaused = True
            self.timer.stop()
            self.pause_btn.setText("⏯ Resume")
        else:
            self.isPaused = False
            self.timer.start(200)
            self.pause_btn.setText("⏸ Pause")

    def reset_plotting(self):
        self.isRunning = True
        self.isPaused = False
        if self.timer.isActive():
            self.timer.stop()
        self.time_history.clear()
        for p in self.parameters:
            self.data[p].clear()
            self.curves[p].setData([], [])
        self.base_curve.setData([], [])
        self.pause_btn.setText("⏸ Pause")

        self.t0 = time.time()
        for cb in self.checkboxes.values():
            cb.setChecked(False)
        first_param = self.parameters[0]
        self.checkboxes[first_param].setChecked(True)
        self.update_selected()
        self.timer.start(200)

    # --- Update ---
    def update_plot(self):
        if not self.isRunning or self.isPaused or self._isClosing:
            return

        # Drain queue, keep only latest (avoid GUI lag)
        latest = None
        try:
            while True:
                latest = self.data_queue.get_nowait()
        except Empty:
            pass

        if latest is None:
            return

        timestamp, values = latest
        self.time_history.append(timestamp - self.t0)
        for p, v in values.items():
            self.data[p].append(v)

        # Only plot if non-empty; convert deque -> list (pyqtgraph expects sequences)
        if len(self.time_history) > 0:
            th = list(self.time_history)
            self.base_curve.setData(th, [0] * len(th))

            for p, cb in self.checkboxes.items():
                if cb.isChecked() and len(self.data[p]) > 0:
                    self.curves[p].setData(th, list(self.data[p]))
                    self.viewboxes[p].enableAutoRange(axis=self.viewboxes[p].YAxis, enable=True)

        self.update_views()


# =========================
#       X-Plane Plugin
# =========================
class PythonInterface:
    def __init__(self):
        self.Name = "ParaViz"
        self.Sig = "plugin003.paraviz.byaryanshukla"
        self.Desc = "Plots Timeseries Data in Real-Time"

        self.parameters = {
            "alt": "sim/flightmodel2/position/pressure_altitude",
            "cas": "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
        }
        self.datarefs_pointer = {}

        self.isPlotting = False
        self.qtThread = None
        self._qt_app = None          # 🟢 CHANGE: owned by GUI thread only
        self.dataQ = Queue()
        self.window = None
        self._stop_requested = threading.Event()  # 🟢 CHANGE: cross-thread stop signal

    def XPluginStart(self):
        self.paravizMenuId = xp.createMenu("ParaViz", None, 0, self.MenuHandler, None)
        self.toggleMenuItemId = xp.appendMenuItem(self.paravizMenuId, "Toggle: ON", 'toggle')

        self.datarefs_pointer = {p: xp.findDataRef(d) for p, d in self.parameters.items()}

        return self.Name, self.Sig, self.Desc

    def XPluginEnable(self): return 1
    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam): pass
    def XPluginDisable(self): pass
    def XPluginStop(self): pass

    def MenuHandler(self, menuRef, itemRef):
        # Toggle ON/OFF from sim thread (safe)
        self.isPlotting = not self.isPlotting
        if self.isPlotting:
            xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: OFF")
            self.StartPlotting()
        else:
            xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: ON")
            self.StopPlotting()

    # 🟢 CHANGE: GUI thread runs its own QApplication; no reuse across runs/threads
    def StartPlotting(self):
        self.qtThread = threading.Thread(target=self.LaunchUI, name="ParaVizQtThread", daemon=True)
        self.qtThread.start()
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 0.1, None)  # 10 Hz
        xp.registerDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)

    def LaunchUI(self):
        # Create app in THIS thread; do not reuse cross-thread
        self._qt_app = QtWidgets.QApplication(sys.argv)
        self.window = PlotterWindow(
            self.dataQ,
            list(self.parameters.keys()),
            notify_stop=self.RequestStop  # 🟢 CHANGE: GUI notifies, sim thread stops
        )
        self.window.setWindowTitle("ParaViz - Live Timeseries")
        self.window.show()

        # Quit app when last window closes
        self._qt_app.setQuitOnLastWindowClosed(True)
        try:
            self._qt_app.exec_()
        finally:
            # GUI thread cleanup
            self.window = None
            self._qt_app = None

    # 🟢 CHANGE: Only set an Event here; safe from any thread
    def RequestStop(self):
        self._stop_requested.set()

    def StopPlotting(self):
        # Called from sim thread (Menu OFF) -> safe to touch xp.*
        # Also handles the case where GUI already initiated stop.
        self._stop_requested.clear()

        # Unregister callbacks first to stop producer
        try:
            xp.unregisterFlightLoopCallback(self.FlightLoopCallback, None)
        except Exception:
            pass
        try:
            xp.unregisterDrawCallback(self.DrawCallback, xp.Phase_Window, 0, 0)
        except Exception:
            pass

        # Ask GUI thread to close the window if it still exists
        if self.window is not None:
            try:
                # 🟢 CHANGE: request close via queued connection (thread-safe)
                QtCore.QMetaObject.invokeMethod(
                    self.window, "close", QtCore.Qt.QueuedConnection
                )
            except Exception:
                # Fallback: best-effort close
                try:
                    self.window.close()
                except Exception:
                    pass

        # Join GUI thread so QApplication fully shuts down
        if self.qtThread is not None and self.qtThread.is_alive():
            self.qtThread.join(timeout=2.0)
        self.qtThread = None

        # Reset menu state if needed
        if self.isPlotting:
            self.isPlotting = False
            try:
                xp.setMenuItemName(self.paravizMenuId, self.toggleMenuItemId, "Toggle: ON")
            except Exception:
                pass

    def FlightLoopCallback(self, elapsedSinceLastCall, elapsedTimeSinceLastFlightLoop, loopCounter, refcon):
        # 🟢 CHANGE: honor stop requested from GUI (called on sim thread)
        if self._stop_requested.is_set():
            self.StopPlotting()
            return 0  # no re-schedule (just in case)

        # Produce latest values
        values = {p: xp.getDataf(dref) for p, dref in self.datarefs_pointer.items()}
        self.dataQ.put((time.time(), values))
        return 0.1  # 10 Hz

    def DrawCallback(self, inPhase, inAfter, inRefCon):
        try:
            screen_width, screen_height = xp.getScreenSize()
            xp.drawString(
                rgb=(1.0, 0.0, 0.0),
                x=screen_width - 250,
                y=screen_height - 20,
                value="PLOTTING TIMESERIES DATA ...",
                fontID=xp.Font_Proportional
            )
        except Exception:
            pass
        return 1
