'''
Author:         Aryan Shukla
Plugin Name:    Custom Command
Tools Used:     Python 3.13.3, XPPython3 4.5.0
'''

from XPPython3 import xp # type: ignore

class PythonInterface:
    def __init__(self):
        self.Name = "Custom Command"
        self.Sig = "aryanshukla.plugin005.customcommand"
        self.Desc = "A Custom Command That Can Change Heading By 10 Degrees"

        self.datarefs = {
            'heading': 'sim/flightmodel/position/mag_psi'
        }

        self.hdgPlus10Cmd = None
    
    def XPluginStart(self):
        self.datarefs_pointers = {
            param: xp.findDataRef(self.datarefs[param])
            for param in self.parameters
        }

        self.hdgPlus10Cmd = xp.createCommand(
            "vimaan/autopilot/heading_plus_10",
            "Increase Heading By 10 Degrees"
        )

        xp.registerCommandHandler(
            self.hdgPlus10Cmd,
            self.hdgPlus10Handler,
            0,
            None
        )

        xp.log("HDG+10 Command Loaded Successfully")

        return self.Name, self.Sig, self.Desc
    
    def hdgPlus10Handler(self, cmdRef, phase, refcon):

        if phase == xp.CommandBegin:
            currentHdg = xp.getDataf(self.datarefs_pointers['heading'])

            newHdg = currentHdg + 10.0
            if newHdg >= 360.0:
                newHdg == 0.0

            xp.setDataf(self.datarefs_pointers['heading'], newHdg)
            xp.log(f"Heading Changed From {currentHdg} To {newHdg}")
        return 1

    def XPluginEnable(self):
        return 1

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def XPluginDisable(self):
        pass

    def XPluginStop(self):
        if self.hdgPlus10Cmd:
            xp.unregisterCommandHandler(
                self.hdgPlus10Cmd,
                self.hdgPlus10Handler,
                0,
                None
            )