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

/*This is an application that listens input angles on UDP port, and drives up to 3 DRV8825 stepper motor drivers.*
* The application is aimed for Raspberry Pi and requires pigpio library installed.*
* Check, and modify if necessary, pinout in pigpio_driver.cpp*/

#include <iostream>
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <vector>
#include <algorithm>
#include <chrono>
#include <csignal>

#include "bresenham.h"
#include "pigpio_driver.h"

struct State {
    bool motor0Enabled;
    float motor0Angle;
    bool motor1Enabled;
    float motor1Angle;
    bool motor2Enabled;
    float motor2Angle;
};

struct StateTime {
    State state;
    std::chrono::steady_clock::time_point timestamp;
};

float ustepsPerDeg = 400.0f / 360.0f * 64.0f; //32 usteps per step for DRV8825, but 64 logical level changes per step, since ustep is done on rising edge only
float maxDegPerS = 360.0f; // maximum revolution velocity
float minDegPerS = 10.0f; // minimum revolution velocity
std::vector<float> oldAngle = {0.0f, 0.0f, 0.0f};
std::vector<int> fullRevs = {0, 0, 0};
std::vector<int>currentUsteps = {0, 0, 0};
std::vector<int>expectedUsteps = {0, 0, 0};
std::vector <int> ustep = {0, 0, 0};
std::vector <int> dir = {0, 0, 0};

std::queue<StateTime> stateQueue;
std::mutex queueMutex;
std::condition_variable queueCondition;

std::chrono::steady_clock::time_point lastTime = std::chrono::steady_clock::now();

int udpListener()
{
    const int PORT = 7755;
    const int BUFFER_SIZE = 24;  // 3 * bool + 3 * float

    int serverSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (serverSocket == -1)
    {
        std::cerr << "UDP socket creation error." << std::endl;
        return -1;
    }
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(PORT);
    serverAddr.sin_addr.s_addr = INADDR_ANY;

    if (bind(serverSocket, reinterpret_cast<struct sockaddr*>(&serverAddr), sizeof(serverAddr)) == -1)
    {
        std::cerr << "Error binding adress to socket." << std::endl;
        close(serverSocket);
        return -1;
    }

    char buffer[BUFFER_SIZE];
    sockaddr_in clientAddr;
    socklen_t clientAddrLen = sizeof(clientAddr);
    while (true)
    {
        State receivedState;
        ssize_t receivedBytes = recvfrom(serverSocket, buffer, sizeof(buffer), 0,
                                        reinterpret_cast<struct sockaddr*>(&clientAddr), &clientAddrLen);
        if (receivedBytes == -1) {
            std::cerr << "Receive data error" << std::endl;
            close(serverSocket);
            return -1;
        }

        std::memcpy(&receivedState, buffer, sizeof(receivedState));
        std::unique_lock<std::mutex> lock(queueMutex);

        StateTime stateTime;
        stateTime.state = receivedState;
        stateTime.timestamp = std::chrono::steady_clock::now();

        stateQueue.push(stateTime);
        queueCondition.notify_one();
    }
    std::cout << "udpListener thread finished" << std::endl;
    return 0;
}

void moveUstep(std::vector<bool> en, std::vector<int> lastStep, std::vector<int> nextStep)
{
    for (size_t i = 0; i < lastStep.size(); ++i) {
        int diff = nextStep[i] - lastStep[i];
        bool enbl = en[i];
        if (diff > 0)
        {
            dir[i] = 1;
            ustep[i] ^= 1; // toggle step 1->0 or 0->1
        }
        else if ( diff < 0)
        {
            dir[i] = 0;
            ustep[i] ^= 1;
        }
        setGpioVals(i, enbl, ustep[i], dir[i]);
    }
}

void dataConsumer()
{
    while (true)
    {
        std::unique_lock<std::mutex> lock(queueMutex);

        queueCondition.wait(lock, [] { return !stateQueue.empty(); });

        StateTime stateTime = stateQueue.front();
        stateQueue.pop();

        lock.unlock();

        State state = stateTime.state;
        std::chrono::steady_clock::time_point nowTime = stateTime.timestamp;
        std::chrono::microseconds::rep interval = std::chrono::duration_cast<std::chrono::microseconds>(nowTime - lastTime).count();

        if (stateQueue.size() > 1) //avoid accumulation of latency
        {
            interval = interval / stateQueue.size();
        }

        lastTime = nowTime;

        std::vector<float> angle;
        std::vector<bool> enbl;
        std::vector<float> totalAngle = {0.0f, 0.0f, 0.0f};
        angle.push_back(state.motor0Angle);
        angle.push_back(state.motor1Angle);
        angle.push_back(state.motor2Angle);
        enbl.push_back(state.motor0Enabled);
        enbl.push_back(state.motor1Enabled);
        enbl.push_back(state.motor2Enabled);

        for (auto iden = 0; iden < 3; iden++)
        {
            float ang = angle[iden];
            float oldAng =  oldAngle[iden];
            if (ang - oldAng > 180.0f) //encoder underflow
            {
                fullRevs[iden]--;
            }
            else if (ang - oldAng < -180.0f) //encoder overflow
            {
                fullRevs[iden]++;
            }
            oldAngle[iden] = ang;
            totalAngle[iden] = fullRevs[iden] * 360.0f + ang;

            std::cout << "Motor "<< iden <<" enabled: " << enbl[iden] << ", Angle: " << totalAngle[iden] << std::endl;

            expectedUsteps[iden] = int(ustepsPerDeg * totalAngle[iden]);
        }
        long maxDist = std::max(std::max(std::abs(expectedUsteps[0] - currentUsteps[0]),
                                std::abs(expectedUsteps[1] - currentUsteps[1])),
                                std::abs(expectedUsteps[2] - currentUsteps[2]));

        std::chrono::microseconds::rep ustepInterval = interval / (maxDist + 1);
        std::chrono::microseconds::rep maxUstepInterval = 1e6 / (minDegPerS * ustepsPerDeg);
        std::chrono::microseconds::rep minUstepInterval = 1e6 / (maxDegPerS * ustepsPerDeg);

        if (ustepInterval > maxUstepInterval)
        {
            ustepInterval = maxUstepInterval;
            std::cout << "Minimum speed exceeded, correcting" << std::endl;
        }
        if (ustepInterval < minUstepInterval)
        {
            ustepInterval = minUstepInterval;
            std::cout << "Maximum speed exceeded, correcting" << std::endl;
        }

        std::vector<std::vector<int>> listOfSteps = b3D(currentUsteps, expectedUsteps); // (x1, y1, z1, x2, y2, z2)
        currentUsteps = expectedUsteps;

        std::vector<int> step = listOfSteps[0]; //enable/disable power without doing a step
        moveUstep(enbl, step, step);

        for (std::size_t i = 0; i < listOfSteps.size() - 1; ++i)
        {
            std::vector<int> lastStep = listOfSteps[i];
            std::vector<int> nextStep = listOfSteps[i + 1];
            moveUstep(enbl, lastStep, nextStep);
            std::this_thread::sleep_for(static_cast<std::chrono::microseconds>(ustepInterval));
        }
    }
}

void signalClb(int signum)
{
    // terminate pigpio
    terminateGpio();
    std::exit(EXIT_SUCCESS);
}

int main(int argc, char* argv[])
{
    for (auto i = 1; i < argc; i++)
    {
        std::string arg = argv[i];
        if (arg=="-steps_per_rev")
        {
            if ((i + 1) < argc)
            {
                std::string s = argv[i + 1];
                float stepsPerRev = std::stof(s);
                ustepsPerDeg = stepsPerRev / 360.0f * 64.0f;
                std::cout << "Steps per motor revolution: " << stepsPerRev << std::endl;
            }
        }
        if (arg=="-max_degs_per_second")
        {
            if ((i + 1) < argc)
            {
                std::string s = argv[i + 1];
                maxDegPerS = std::stof(s);
                std::cout << "Degrees per second MAX velocity: " << maxDegPerS << std::endl;
            }
        }
        if (arg=="-min_degs_per_second")
        {
            if ((i + 1) < argc)
            {
                std::string s = argv[i + 1];
                minDegPerS = std::stof(s);
                std::cout << "Degrees per second MIN velocity: " << minDegPerS << std::endl;
            }
        }
        if (arg=="-h")
        {
            std::cout << "-steps_per_rev Sets number of full steps for a single motor revolution" << std::endl;
            std::cout << "-max_degs_per_second Limits maximum motor speed in degrees per second" << std::endl;
            std::cout << "-min_degs_per_second Limits minimum motor speed in degrees per second" << std::endl;
        }
    }

    if (initGpio() < 0)
    {
        std::cout << "pigpio initialisation failed" << std::endl;
        return -1;
    }
    std::signal(SIGINT, signalClb); // signal callback for cleaning resources after Ctrl-C
    std::cout << "Size of State structure: " << sizeof(State) << " bytes" << std::endl;
    std::thread udpThread(udpListener);
    std::thread consumerThread(dataConsumer);

    udpThread.join();
    consumerThread.join();

    return 0;
}
