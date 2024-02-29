# Script showing driving assembly movement with spreadsheet
# Can be combined with motor-observer.py for driving stepper motors, motor-observer.py have to be loaded before this script
# Use spreadsheet-example-deltarobot.FCStd as example input model

import FreeCAD as App
import FreeCADGui as Gui
from PySide2 import QtCore

timer_pose = QtCore.QTimer()
timer_pose.setSingleShot(True)
timer_pose.setInterval(0)

initial_row = 2
row_idx = initial_row
end_of_data = False
looped = False

pos = [0, 0, 0]

def update_pose():
    global end_of_data, row_idx # required if triggered by timer
    if not end_of_data:
        try:
            pos[0] = App.ActiveDocument.Spreadsheet.get("A"+str(row_idx))
            pos[1] = App.ActiveDocument.Spreadsheet.get("B"+str(row_idx))
            pos[2] = App.ActiveDocument.Spreadsheet.get("C"+str(row_idx))
            for p in pos:
                is_num = isinstance(p, (int, float))
                if not is_num:
                    App.Console.PrintMessage("Position not a number at row: " + str(row_idx) + " breaking\n")
                    return
            duration = App.ActiveDocument.Spreadsheet.get("D"+str(row_idx))
            is_num = isinstance(duration, (int, float))
            if not is_num:
                App.Console.PrintMessage("Duration not a number at row: " + str(row_idx) + " breaking\n")
                return
            print (pos)
            App.ActiveDocument.getObjectsByLabel('PlatePosition')[0].Placement = App.Placement(App.Vector(pos),App.Rotation(App.Vector(0,0,1),0)) # modyfying fixed joint
            Gui.runCommand('Assembly_SolveAssembly',0) # update other joint - solve asm
            timer_pose.setInterval(duration * 1000)
            timer_pose.start()
            row_idx = row_idx + 1
        except:
            if looped:
                row_idx = initial_row
                duration = App.ActiveDocument.Spreadsheet.get("D"+str(row_idx))
                timer_pose.setInterval(duration * 1000)
                timer_pose.start()
            else:
                end_of_data = True
                App.Console.PrintMessage("Enf of data at row: " + str(row_idx) + " ending\n")

timer_pose.timeout.connect(update_pose)
timer_pose.start()
