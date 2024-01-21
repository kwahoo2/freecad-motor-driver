/**************************************************************************
*                                                                         *
*   Copyright (c) 2024 Adrian Przekwas adrian.v.przekwas@gmail.com        *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU Lesser General Public License (LGPL)    *
*   as published by the Free Software Foundation; either version 3 of     *
*   the License, or (at your option) any later version.                   *
*   for detail see the LICENCE text file.                                 *
*                                                                         *
*   This program is distributed in the hope that it will be useful,       *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU Library General Public License for more details.                  *
*                                                                         *
*   You should have received a copy of the GNU Library General Public     *
*   License along with this program; if not, write to the Free Software   *
*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
*   USA                                                                   *
*                                                                         *
***************************************************************************/

#include <iostream>
#include <pigpio.h>
#include "pigpio_driver.h"

static const int enablPin0 = 4; // GPIO 4, physical pin 7
static const int enablPin1 = 20; // GPIO 20, physical pin 38
static const int enablPin2 = 17; // GPIO 17, physical pin 11
static const int dirPin0 = 5; // GPIO 5, physical pin 29
static const int stepPin0 = 6; // GPIO 6, physical pin 31
static const int dirPin1 = 12; // GPIO 12, physical pin 32
static const int stepPin1 = 26; // GPIO 26, physical pin 37
static const int dirPin2 = 27; // GPIO 27, physical pin 13
static const int stepPin2 = 22; // GPIO 22, physical pin 15

int  initGpio(void)
{
    if (gpioInitialise() < 0)
   {
      return -1;
   }


    /* Set GPIO modes */
    gpioSetMode(enablPin0, PI_OUTPUT);
    gpioSetMode(dirPin0, PI_OUTPUT);
    gpioSetMode(stepPin0, PI_OUTPUT);
    gpioSetMode(enablPin1, PI_OUTPUT);
    gpioSetMode(dirPin1, PI_OUTPUT);
    gpioSetMode(stepPin1, PI_OUTPUT);
    gpioSetMode(enablPin2, PI_OUTPUT);
    gpioSetMode(dirPin2, PI_OUTPUT);
    gpioSetMode(stepPin2, PI_OUTPUT);

    /*set initial values*/
    gpioWrite(enablPin0, 1);
    gpioWrite(enablPin1, 1);
    gpioWrite(enablPin2, 1);
    gpioWrite(stepPin0, 0);
    gpioWrite(stepPin1, 0);
    gpioWrite(stepPin2, 0);
    gpioWrite(dirPin0, 0);
    gpioWrite(dirPin1, 0);
    gpioWrite(dirPin2, 0);

    return 0;
}

void terminateGpio(void)
{
    std::cout << "Terminating, releasing resources..." << std::endl;
    gpioTerminate();
}

void setGpioVals(int i, bool enbl, int uVal, int dVal)
{
    //std::cout << "Motor: "<< i << " " << enbl << " " << uVal << " " << dVal << std::endl;
    switch (i)
    {
        case 0:
        {
            enbl ? gpioWrite(enablPin0, 0) : gpioWrite(enablPin0, 1); //DRV 8825 ENBL low active
            dVal ? gpioWrite(dirPin0, 1) : gpioWrite(dirPin0, 0);
            uVal ? gpioWrite(stepPin0, 1) : gpioWrite(stepPin0, 0);
            break;
        }
        case 1:
        {
            enbl ? gpioWrite(enablPin1, 0) : gpioWrite(enablPin1, 1);
            dVal ? gpioWrite(dirPin1, 1) : gpioWrite(dirPin1, 0);
            uVal ? gpioWrite(stepPin1, 1) : gpioWrite(stepPin1, 0);
            break;
        }
        case 2:
        {
            enbl ? gpioWrite(enablPin2, 0) : gpioWrite(enablPin2, 1);
            dVal ? gpioWrite(dirPin2, 1) : gpioWrite(dirPin2, 0);
            uVal ? gpioWrite(stepPin2, 1) : gpioWrite(stepPin2, 0);
            break;
        }
        default:
            break;
    }
}
