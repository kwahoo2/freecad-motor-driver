# An example of using a VR motion controller to move 3 axis robot
# SteamVR and pyopenvr is required
# The code is simple but usage is a bit tricky:
# 1. Paste the code in FreeCAD
# 2. Open the 3axis_robot_forced_simplified.FCStd file
# 3. Double click on the assembly in the tree view to activate it
# 4. Type vri = Vri() to start tracking and solving the assembly (to stop type: vri.stop())
# 5. On the Pi execute sudo ./udp_receiver -min_degs_per_second 0
# 6. The arm will only move when the controller trigger is pressed

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2024 Adrian Przekwas adrian.v.przekwas@gmail.com        *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 3 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD as App, FreeCADGui as Gui, Part, time, sys, math
from PySide2 import QtGui, QtCore
import UtilsAssembly
from pivy import coin
import openvr
import struct
import socket
import time
import platform

class MotorObserver:
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink","SupportObject","MotorObserver","Support for observer placement")
        obj.addProperty("App::PropertyRotation","BaseRotation","MotorObserver","Base Rotation")
        obj.addProperty("App::PropertyAngle","TransfAngle","MotorObserver","Angle of Transformation")
        obj.addProperty("App::PropertyBool","Enabled","MotorObserver","Enable the motor").Enabled = True
        obj.addProperty("App::PropertyBool","Reversed","MotorObserver","Reverse motor direction").Reversed = False
        obj.setEditorMode("TransfAngle", 1) # this property should be read only
        obj.Proxy = self

    def onChanged(self, fp, prop):
        if (prop == "SupportObject"):
            if (fp.SupportObject):
                App.Console.PrintMessage(str(fp.Label) + " Support: " + str(fp.SupportObject.Label) + "\n")
        if (prop == "Placement") or (prop == "Enabled"):
            auto_set_base_pl = False
            rot = fp.Placement.Rotation
            base_rot = fp.BaseRotation
            # if the observer is moving in 3D space it need a support object specified
            # eg.: if observer is fixed to a motor pulley, the motor housing can used as a support object
            # an user can set the support in the data tab inside FreeCAD window
            if (fp.SupportObject):
                support_rot = fp.SupportObject.Placement.Rotation
                transf_rot = base_rot.inverted() * support_rot.inverted() * rot
            else:
                transf_rot = base_rot.inverted() * rot # calculate how much rotation is transformed from initial rotation
            axis = transf_rot.Axis
            angle = transf_rot.Angle
            revers = fp.Reversed
            enbl = fp.Enabled
            if revers:
                angle = 2 * math.pi - angle
            if (axis.x > 0.99 or axis.y > 0.99 or axis.z > 0.99):
                pass
            elif (axis.x < -0.99 or axis.y < -0.99 or axis.z < -0.99): # reverse angle if axis -1
                angle = 2 * math.pi - angle
            else:
                App.Console.PrintWarning("Multiple axis rotation, breaking!\n")
                if auto_set_base_pl:
                    if (fp.SupportObject):
                        fp.BaseRotation = fp.SupportObject.Placement.Rotation.inverted() * fp.Placement.Rotation
                    else:
                        fp.BaseRotation = rot
                    App.Console.PrintMessage("Base rotation adjusted automatically\n")
                return
            fp.TransfAngle = str (angle) + 'rad'

    def execute(self, fp):
        w = 10
        l = 7
        h = 3
        fp.Shape = Part.makeBox(w, l, h, App.Vector(-w / 2, -l / 2, -h / 2))

class Vri(object):
    def __init__(self):
        default_remote = '192.168.1.23' # edit this adress if you are running remote Raspberry Pi as backend
        if (platform.machine() == 'armv7l') or (platform.machine() == 'aarch64'): # assumes running on Pi that drives steppers directly
            self.adr = '127.0.0.1'
        else:
            self.adr = default_remote
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.vr = openvr.init(openvr.VRApplication_Other)
        self.vrsystem = openvr.VRSystem()
        self.poses = []  # will be populated with proper type after first call
        App.Console.PrintMessage('init')
        App.ActiveDocument.recompute()
        self.base_transl = coin.SbVec3f()
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.placement_update)
        self.timer.start(100)
        self.timer_states = QtCore.QTimer()
        QtCore.QObject.connect(self.timer_states, QtCore.SIGNAL("timeout()"), self.states_update)
        time.sleep(0.1)
        self.timer_states.start(500) # states updated slower than asm for less stepper jitter
        App.Console.PrintMessage('timers started')

    def extracttranslation(self, transfmat):
        pos = coin.SbVec3f(transfmat[0][3], transfmat[1][3], transfmat[2][3])
        return pos

    def placement_update(self):
        self.poses = self.vr.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount)
        for i in range(1, len(self.poses)):
            pose = self.poses[i]
            if not pose.bDeviceIsConnected:
                continue
            if not pose.bPoseIsValid:
                continue
            device_class = openvr.VRSystem().getTrackedDeviceClass(i)
            if not device_class == openvr.TrackedDeviceClass_Controller:
                continue
            controllerPose = pose.mDeviceToAbsoluteTracking
            result, pControllerState = self.vrsystem.getControllerState(i)
            conpos = self.extracttranslation(controllerPose) * 1000 # meters to milimeters
            trigval = pControllerState.rAxis[1].x # trgger value 0.0 - 1.0
            # very simple CS transformation, since we don't need Rotation in this example
            # adjust for your LH placement
            fc_trans = App.Vector(-conpos[2], -conpos[0], conpos[1])
            # moving_obj = App.ActiveDocument.getObject('Box')
            moving_obj = App.ActiveDocument.getObjectsByLabel("GroundedSphereJoint")[0]
            if trigval < 0.5: # if trigger not pressed, change placement offset
                self.base_transl = fc_trans - moving_obj.Placement.Base
            else:
                moving_obj.Placement=App.Placement((fc_trans - self.base_transl), App.Rotation())
            assembly = UtilsAssembly.activeAssembly()
            if not assembly:
                return
            assembly.solve()

    def states_update(self):
            observers = App.ActiveDocument.findObjects(Label="MotorObserver")
            states_for_send = []
            for iden, obs in enumerate(observers):
                state = [bool(obs.Enabled), float(obs.TransfAngle.Value)]
                if len(states_for_send) < 3:
                    states_for_send.append(state)
                else:
                    App.Console.PrintError(str(obs.Label) + "not added, max 3 motors per group allowed!\n")
                App.Console.PrintMessage(str(obs.Label) + " " + str(state) + "\n")
            while len(states_for_send) < 3:
                iden = len(states_for_send)
                states_for_send.append([False, 0.0])
                App.Console.PrintMessage("Dummy" + str(iden) + "motor added for padding\n")
            self.send_states_udp(states_for_send)

    def send_states_udp(self, states_for_send):
        format_string = "?f" * len(states_for_send)
        packed_states = struct.pack(format_string, *(item for sublist in states_for_send for item in sublist))
        if (self.sock and not self.sock._closed):
            App.Console.PrintMessage("States changed, sending MotorObservers\n")
            sent = self.sock.sendto(packed_states, (self.adr, 7755))

    def stop(self):
        self.timer.stop()
        openvr.shutdown()
        self.sock.close()

# vri = Vri() # paste without comment to start

# To stop the animation, type:
# vri.stop()
