'''
Author:         Aryan Shukla
Plugin Name:    Heading Target Controller
Tools Used:     Python 3.13.3, XPPython3 4.5.0
'''

from XPPython3 import xp  # type: ignore


class PythonInterface:
    def __init__(self):
        self.Name = "Heading Target Controller"
        self.Sig = "aryanshukla.plugin.headingtarget"
        self.Desc = "Smoothly Rotate Heading Knob To Fixed Target Heading"

        # ------------------------------------------------------------
        # CONFIGURATION
        # ------------------------------------------------------------
        self.TARGET_HEADING = 20.0      # <<< CHANGE TARGET HERE (0–359)
        self.STEP_INTERVAL = 0.1        # seconds per degree (animation speed)

        # ------------------------------------------------------------
        # X-Plane handles
        # ------------------------------------------------------------
        self.hdgDialDR = None
        self.hdgUpCmd = None
        self.hdgDownCmd = None
        self.mainCmd = None

        # ------------------------------------------------------------
        # Motion state
        # ------------------------------------------------------------
        self.stepsRemaining = 0
        self.direction = 0              # +1 = up, -1 = down
        self.flightLoopActive = False

    # ============================================================
    # Plugin start
    # ============================================================
    def XPluginStart(self):

        xp.log(">>> Heading Target Plugin: XPluginStart <<<")

        # Find heading selector DataRef
        self.hdgDialDR = xp.findDataRef(
            "sim/cockpit2/autopilot/heading_dial_deg_mag_pilot"
        )

        # Find sim commands that drive the knob animation
        self.hdgUpCmd = xp.findCommand("sim/autopilot/heading_up")
        self.hdgDownCmd = xp.findCommand("sim/autopilot/heading_down")

        # Create custom command
        self.mainCmd = xp.createCommand(
            "vimaan/autopilot/heading_go_to_target",
            "Rotate Heading Knob To Target Heading"
        )

        xp.registerCommandHandler(
            self.mainCmd,
            self.commandHandler,
            0,
            None
        )

        xp.log(">>> Heading Target Plugin READY <<<")
        return self.Name, self.Sig, self.Desc

    # ============================================================
    # Command handler
    # ============================================================
    def commandHandler(self, cmdRef, phase, refcon):

        if phase != xp.CommandBegin:
            return 1

        # If animation already running, ignore new command
        if self.flightLoopActive:
            xp.log(">>> Rotation already in progress <<<")
            return 1

        current = xp.getDataf(self.hdgDialDR) % 360.0
        target = self.TARGET_HEADING % 360.0

        # Compute shortest path
        cw = (target - current) % 360.0
        ccw = (current - target) % 360.0

        if cw <= ccw:
            self.direction = +1
            self.stepsRemaining = int(round(cw))
        else:
            self.direction = -1
            self.stepsRemaining = int(round(ccw))

        xp.log(
            f">>> Rotate HDG {current:.1f} → {target:.1f} | "
            f"Steps={self.stepsRemaining} | "
            f"Dir={'UP' if self.direction > 0 else 'DOWN'}"
        )

        if self.stepsRemaining > 0:
            xp.registerFlightLoopCallback(
                self.flightLoop,
                self.STEP_INTERVAL,
                None
            )
            self.flightLoopActive = True

        return 1

    # ============================================================
    # Flight loop callback (smooth animation)
    # ============================================================
    def flightLoop(self, elapsedMe, elapsedSim, counter, refcon):

        if self.stepsRemaining <= 0:
            xp.log(">>> Heading rotation complete <<<")

            xp.unregisterFlightLoopCallback(self.flightLoop, None)
            self.flightLoopActive = False
            return 0

        if self.direction > 0:
            xp.commandOnce(self.hdgUpCmd)
        else:
            xp.commandOnce(self.hdgDownCmd)

        self.stepsRemaining -= 1
        return self.STEP_INTERVAL

    # ============================================================
    # Required callbacks
    # ============================================================
    def XPluginEnable(self):
        xp.log(">>> Plugin Enabled <<<")
        return 1

    def XPluginDisable(self):
        xp.log(">>> Plugin Disabled <<<")

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def XPluginStop(self):
        xp.log(">>> Plugin Stopping <<<")

        if self.flightLoopActive:
            xp.unregisterFlightLoopCallback(self.flightLoop, None)
            self.flightLoopActive = False
