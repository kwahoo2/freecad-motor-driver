/**************************************************************************
*                                                                         *
*   Copyright (c) 2024 Adrian Przekwas adrian.v.przekwas@gmail.com        *
*                                                                         *
*   Inspired by the article:                                              *
*   www.geeksforgeeks.org/bresenhams-algorithm-for-3-d-line-drawing       *
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


/* Inspired by https://www.geeksforgeeks.org/bresenhams-algorithm-for-3-d-line-drawing/
 */
#include <cmath>
#include <iostream>

#include "bresenham.h"

std::vector<std::vector<int>> b3D(std::vector<int> cUSteps, std::vector<int> expUsteps)
{
    std::vector<std::vector<int>> listOfSteps;
    listOfSteps.push_back(cUSteps);

    int x1 = cUSteps[0];
    int y1 = cUSteps[1];
    int z1 = cUSteps[2];
    int x2 = expUsteps[0];
    int y2 = expUsteps[1];
    int z2 = expUsteps[2];

    int dx = abs(x2 - x1);
    int dy = abs(y2 - y1);
    int dz = abs(z2 - z1);
    int xs = (x2 > x1) ? 1 : -1;
    int ys = (y2 > y1) ? 1 : -1;
    int zs = (z2 > z1) ? 1 : -1;

    if (dx >= dy && dx >= dz)
	{
        int p1 = 2 * dy - dx;
        int p2 = 2 * dz - dx;
        while (x1 != x2)
		{
            x1 += xs;
            if (p1 >= 0)
			{
                y1 += ys;
                p1 -= 2 * dx;
            }
            if (p2 >= 0)
			{
                z1 += zs;
                p2 -= 2 * dx;
            }
            p1 += 2 * dy;
            p2 += 2 * dz;
            listOfSteps.push_back({x1, y1, z1});
        }
    }
    else if (dy >= dx && dy >= dz)
	{
        int p1 = 2 * dx - dy;
        int p2 = 2 * dz - dy;
        while (y1 != y2) {
            y1 += ys;
            if (p1 >= 0)
			{
                x1 += xs;
                p1 -= 2 * dy;
            }
            if (p2 >= 0)
			{
                z1 += zs;
                p2 -= 2 * dy;
            }
            p1 += 2 * dx;
            p2 += 2 * dz;
            listOfSteps.push_back({x1, y1, z1});
        }
    }
    else
	{
        int p1 = 2 * dy - dz;
        int p2 = 2 * dx - dz;
        while (z1 != z2)
		{
            z1 += zs;
            if (p1 >= 0)
			{
                y1 += ys;
                p1 -= 2 * dz;
            }
            if (p2 >= 0)
			{
                x1 += xs;
                p2 -= 2 * dz;
            }
            p1 += 2 * dy;
            p2 += 2 * dx;
            listOfSteps.push_back({x1, y1, z1});
        }
    }
    return listOfSteps;
}
