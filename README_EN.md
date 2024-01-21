# FreeCAD stepper motors driver

The goal of the project is to show how stepper motors can be controlled directly from FreeCAD.
The example uses a Raspberry Pi and common DRV8825 drivers for synchronized control of up to 3 stepper motors.

## Requirements

To start controlling stepper motors from FreeCAD, you need:

### Hardware

* Raspberry Pi.
* 1 to 3 stepper motors.
* 1 to 3 DRV8825 controllers.
* (Optional) another computer if control is to be done remotely.

### Software

* pigpio libraries installed on Raspberry Pi.
* FreeCAD or Ondsel ES installed on the Raspberry Pi or on a remote computer.

## Contents of the repository

The content of the repository is divided into 3 parts, located in the following directories:

* motor-observer - a Python script that is used to create "MotorObserver" objects in FreeCAD and monitor their movement.
* udp-receiver - a program for Raspberry Pi that receives input from `motor-oberver.py` and controls the stepper motors.
* deltarobot-example - an example of a delta robot model built in FreeCAD/Ondsel ES's integrated assembly environment.

### Running the example.

* Download the contents of the repository:

`git clone https://github.com/kwahoo2/freecad-motor-driver.git`

* Install the pigpio libraries on the Raspberry Pi:

`sudo apt install pigpio`

* Compile the contents of the udp-receiver directory while on the Raspberry Pi:

`make`

* Download [Ondsel ES](https://github.com/Ondsel-Development/FreeCAD/releases) (FreeCAD version with unified assembly workbench implemented) and execute it.
After starting, paste the contents of the `motor-observer.py` script into the Python console and **then** open the `deltarobot-example.FCStd` example.
Note: if you are running FreeCAD on a remote computer, adjust the line `default_remote = '192.168.1.23'` in the `motor-observer.py` script by entering the IP address of the Raspberry Pi there. You can also change the address after the script starts by typing `adr='192.168.XXX.XXX` in the interpreter.

* Run the motor driver application on the Raspberry Pi (requires superuser rights due to GPIO access):

`sudo ./udp-receiver`

* Move the assembly with the mouse, after activating it by double-clicking on the `deltabot` assembly in the feature tree. In the Ondsel/FreeCAD report view, you should see something similar to:

```
15:53:03  MotorObserver0 [True, 8.391769606205315]
15:53:03  MotorObserver1 [True, 6.743947165727947]
15:53:03  MotorObserver2 [True, 1.9981262137739997]
15:53:03  States changed, sending MotorObservers
```

and in the terminal window after executing `udp-receiver`:

```
Motor 0 enabled: 1, Angle: 8.39177
Motor 1 enabled: 1, Angle: 6.74395
Motor 2 enabled: 1, Angle: 1.99813
```

![Main Window][mw]

[mw]: https://raw.githubusercontent.com/kwahoo2/freecad-motor-driver/main/.github/images/mw_en.png "Main Window"

## Connecting DRV8825 drivers
Pinout for 3 drivers is defined in `pigpio_driver.cpp`:

```
static const int enablPin0 = 4; // GPIO 4, physical pin 7
static const int enablPin1 = 20; // GPIO 20, physical pin 38
static const int enablPin2 = 17; // GPIO 17, physical pin 11
static const int dirPin0 = 5; // GPIO 5, physical pin 29
static const int stepPin0 = 6; // GPIO 6, physical pin 31
static const int dirPin1 = 12; // GPIO 12, physical pin 32
static const int stepPin1 = 26; // GPIO 26, physical pin 37
static const int dirPin2 = 27; // GPIO 27, physical pin 13
static const int stepPin2 = 22; // GPIO 22, physical pin 15
```

## Create a new observer object

After creating a new document, you can create a new MotorObserver object by typing in the FreeCAD console:
`create_observer()`

Move it to the target position and attach it to the tracked axis, for example using the `Create a Fixed Joint` constraint. Then set the current position as the base position:
`set_base_pl()`

After rotating the object, you should see the _Transf Angle_ attribute change and in the FreeCAD console:

```
16:21:19 MotorObserver0 [True, 17.000000000000004]
16:21:19 Dummy1motor added for padding
16:21:19 Dummy2motor added for padding
16:21:19 States changed, sending MotorObservers
```


![Single Observer][so]

[so]: https://raw.githubusercontent.com/kwahoo2/freecad-motor-driver/main/.github/images/single_observer.png "Observer"

