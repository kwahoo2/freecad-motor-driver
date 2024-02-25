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

default_remote = '192.168.1.23' # edit this adress if you are running remote Raspberry Pi as backend

import FreeCAD as App
import Part
import math
from PySide2 import QtCore
import struct
import socket
import time
import platform

recorded_states = []
recording_enabled = False
immediate_send_enabled = True

class MotorObserver:
    def __init__(self, obj):
        '''"App two point properties" '''
        obj.addProperty("App::PropertyLink","SupportObject","MotorObserver","Support for observer placement")
        obj.addProperty("App::PropertyPlacement","BasePlacement","MotorObserver","Base Placement")
        obj.addProperty("App::PropertyAngle","TransfAngle","MotorObserver","Angle of Transformation")
        obj.addProperty("App::PropertyBool","Enabled","MotorObserver","Enable the motor").Enabled = True
        obj.addProperty("App::PropertyBool","Reversed","MotorObserver","Reverse motor direction").Reversed = False
        obj.setEditorMode("TransfAngle", 1) # this property should be read only

        obj.Proxy = self
        self.last_state = []

    def onChanged(self, fp, prop):
        if (prop == "SupportObject"):
            print (fp.SupportObject)

        if (prop == "Placement") or (prop == "Enabled"):
            fp.recompute()
            enbl = fp.Enabled
            angle = fp.TransfAngle.Value
            state = [bool(enbl), float(angle)]
            if (self.last_state == state):
                print("State not changed, pass")
            else:
                try:
                    trigger_sender()
                except:
                    print("No send_states() function defined!")

    def execute(self, fp):
        '''"Print a short message when doing a recomputation, this method is mandatory" '''
        auto_set_base_pl = True
        pl = fp.Placement
        base_pl = fp.BasePlacement
        if (fp.SupportObject):
            support_pl = fp.SupportObject.Placement
            base_pl = support_pl * base_pl
        transf_pl = base_pl.inverse() * pl # calculate how much placement is transformed from initial placement
        axis = transf_pl.Rotation.Axis
        angle = transf_pl.Rotation.Angle
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
                fp.BasePlacement = pl
                App.Console.PrintMessage("Base placement adjusted automatically\n")
            return
        fp.TransfAngle = str (angle) + 'rad'
        w = 10
        l = 7
        h = 3
        fp.Shape = Part.makeBox(w, l, h, App.Vector(-w / 2, -l / 2, -h / 2))

# above class must be defined (pasted in the interpreter) before opening a file with motorobserver addObject
# otherwise will throw pyException: <string>(2)<class 'AttributeError'>: Module __main__ has no class MotorObserver


def create_observer():
    obs_count = len(App.ActiveDocument.findObjects(Label="MotorObserver"))
    obs=App.ActiveDocument.addObject("Part::FeaturePython","MotorObserver" +str(obs_count))
    MotorObserver(obs)
    obs.ViewObject.Proxy=0 # just set it to something different from None (this assignment is needed to run an internal notification)
    obs.recompute()


def set_base_pl(): #set base placement, used to calculate diff angle
    observers = App.ActiveDocument.findObjects(Label="MotorObserver")
    for obs in observers:
        if obs.SupportObject:
            obs.BasePlacement = obs.Placement * obs.SupportObject.Placement
        else:
            obs.BasePlacement = obs.Placement
        obs.recompute()

timer_sender = QtCore.QTimer()
timer_sender.setSingleShot(True)
timer_sender.setInterval(50)

timer_finished = True
sock = None

def send_states():
    observers = App.ActiveDocument.findObjects(Label="MotorObserver")
    states_for_send = []
    for iden, obs in enumerate(observers):
        state = [bool(obs.Enabled), float(obs.TransfAngle.Value)]
        obs.Proxy.last_state = state
        if len(states_for_send) < 3:
            states_for_send.append(state)
        else:
            App.Console.PrintError(str(obs.Label) + "not added, max 3 motors per group allowed!\n")
        print (obs.Label, state)
    while len(states_for_send) < 3:
        iden = len(states_for_send)
        states_for_send.append([False, 0.0])
        App.Console.PrintMessage("Dummy" + str(iden) + "motor added for padding\n")
    if recording_enabled:
        recorded_states.append(states_for_send)
    if immediate_send_enabled:
        send_states_udp(states_for_send)
    global timer_finished
    timer_finished = True

def send_states_udp(states_for_send):
    format_string = "?f" * len(states_for_send)
    packed_states = struct.pack(format_string, *(item for sublist in states_for_send for item in sublist))
    if (sock and not sock._closed):
        App.Console.PrintMessage("States changed, sending MotorObservers\n")
        sent = sock.sendto(packed_states, (adr, 7755))

timer_sender.timeout.connect(send_states)

def trigger_sender():
    if (timer_finished):
        timer_sender.start()

def record_states(enabled, reset = True, send_and_rec = True):
    global recording_enabled, immediate_send_enabled
    recording_enabled = enabled
    immediate_send_enabled = send_and_rec
    if enabled and reset:
        recorded_states.clear()
    App.Console.PrintMessage("Recording states: " + str(recording_enabled) + "Current number: " + str(len(recorded_states)) + "\n")

def replay_states(interval = 100):
    l = len (recorded_states)
    for i, sfs in enumerate(recorded_states):
        send_states_udp(sfs)
        App.Console.PrintMessage("Sent " + str (i + 1) + "of" + str(l) + "\n")
        time.sleep(interval / 1000)

def mo_help():
    App.Console.PrintMessage("Type: adr='127.0.0.1' to use local machine as target or adr='192.168.1.23', where '192.168.1.23' is the IP adress of your remote machine \n Type: sock.close() to close the connection \n Type: create_observer() to create a new MotorObserver object \n Type: set_base_pl() to set initial placement of observers \n")
    App.Console.PrintMessage("Type: record_states(True) to START recording movement \n Type: record_states(False) to STOP recording movement \n Type: replay_states(200) to replay movement with 200ms interval \n")

if (platform.machine() == 'armv7l') or (platform.machine() == 'aarch64'): # assumes running on Pi that drives steppers directly
    adr = '127.0.0.1'
else:
    adr = default_remote

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

App.Console.PrintMessage("Data target set to: " + str(adr) + "\n")
App.Console.PrintMessage("Type mo_help() for help \n")
