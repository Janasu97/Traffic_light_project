#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
import run_stats

import os
import sys
import optparse
import valueCalc
from visualisation import plotWaitingTimes
import numpy as np
from numpy.random import rand
from numpy.random import randn
import random
import math


# the directory in which this script resides
THISDIR = os.path.dirname(__file__)
tripinfoOutput = "network/statistics/real_tripinfo.xml"

# File names
# tll - traffic light times

# we need to import python modules from the $SUMO_HOME/tools directory
# If the environment variable SUMO_HOME is not set, try to locate the python
# modules relative to this script
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from sumolib import checkBinary


# minimum green time for the vehicles
# MIN_GREEN_TIME_NS = 10
MIN_GREEN_TIME_NS = 10


# Green states in W-E and N-S directions
GREENSTATE_WE = 0
GREENSTATE_NS = 2

# the id of the traffic light (there is only one). This is identical to the
# id of the controlled intersection (by default)
TLSID = 'gneJ1'
TLSID2 = 'gneJ2'
disabledPed = 'pType_0'
disablePedArr = []
# pedestrian edges and crossings in W->E and E->W direction
WALKINGAREAS_WE = [':M1_w0', ':M1_w1', ':M1_w2', ':M1_w3', ':M2_w0', ':M2_w1', ':M2_w2', ':M2_w3']
CROSSINGS_WE = [':M1_c0', ':M1_c1', ':M2_c0', ':M2_c2']

# pedestrian edges and crossings in N->S and S->N direction
WALKINGAREAS_NS = [':M1_w0', ':M1_w3', ':M2_w0', ':M2_w1']
CROSSINGS_NS = [':M1_c2', ':M2_c1']

# Type of disabled pedestrians
disabledPed = 'pType_0'


def run():
    """execute the TraCI control loop"""
    # track the duration for which the green phase of the vehicles has been
    # active
    tracicounter = 0


    #Induction loop
    loopNS = False
    loopSN = False


    # main loop. do something every simulation step until no more vehicles are
    # loaded or running
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        tracicounter += 1
        # totalPedRedLight += calcredlightped(CROSSINGS_WE, CROSSINGS_NS, pedRedLight=0)

        # # decide whether there is a waiting pedestrian and switch if the green
        # # phase for the vehicles exceeds its minimum duration
        activeRequest_WE = checkWaitingPersons(WALKINGAREAS_WE, CROSSINGS_WE)
        if activeRequest_WE == True:
            asdas = 65

        # To secure that program is running algorithm set by user
        if tracicounter == 1:
            setTlS1Logic(0, 0, greentimeWE, greentimeNS)
            setTlS2Logic(0, 0, greentimeWE, greentimeNS)


        # Induction loop functionality
        if traci.trafficlight.getPhase(TLSID2) == 0 and loopSN == True:
            loopSN = False
            setTlS2Logic(0, 0, greentimeWE, greentimeNS)

        if traci.trafficlight.getPhase(TLSID) == 0 and loopNS == True:
            loopNS = False
            setTlS1Logic(0, 0, greentimeWE, greentimeNS)

        if loopNS == False:
            if traci.trafficlight.getPhase(TLSID) == 5:
                trigLoopNS = traci.inductionloop.getLastStepVehicleNumber('loop_N_S')
                if trigLoopNS != 0:
                    setTlS1Logic(5, 1, greentimeWE, greentimeNS)
                    loopNS = True

        if loopSN == False:
            if traci.trafficlight.getPhase(TLSID2) == 2:
                trigLoopSN = traci.inductionloop.getLastStepVehicleNumber('loop_S_N')
                if trigLoopSN != 0:
                    setTlS2Logic(2, 1, greentimeWE, greentimeNS)
                    loopSN = True
        # Induction loop functionality

    sys.stdout.flush()
    traci.close()

    # return simulation results
    meanWaitingTimeList = []
    stdeviationList = []
    childrenVeh, childrenPed = valueCalc.getXMLValues(tripinfoOutput)
    meanWaitingTime = valueCalc.waitingTimeCalc(childrenVeh)
    meanWaitingTimeList.append(meanWaitingTime)
    stdeviation = valueCalc.stdDevCalc(childrenVeh)
    stdeviationList.append(stdeviation)
    std = math.sqrt(sum(np.power(stdeviationList, 2)) / len(stdeviationList))
    return meanWaitingTime, std

def addString(text, number):
    return text.replace(".xml", "_" + str(number) + ".xml").replace(".sumocfg", "_" + str(number) + ".sumocfg")

# Detect special needs pedestrians waiting for the green phase to cross the street
def checkWaitingPersons(walkingAreas, crossings):
    """check whether a person has requested to cross the street"""

    # check both sides of the crossing
    for edge in walkingAreas:
        peds = traci.edge.getLastStepPersonIDs(edge)
        # check who is waiting at the crossing
        # we assume that pedestrians are detected upon approaching the crossing after
        # standing still for 2s

        for ped in peds:
            if traci.person.getTypeID(ped) == disabledPed:
                if (traci.person.getWaitingTime(ped) >= 2 and
                        traci.person.getNextEdge(ped) in crossings):
                    return True
    return False

# Calculate the amount of time special needs pedestrians spent on the red light
def calcredlightped(crossings_WE, crossings_NS, pedRedLight):
    # Check for the pedestrians currently on the crossings
    for edge in crossings_WE:
        peds = traci.edge.getLastStepPersonIDs(edge)

        for ped in peds:

            if traci.person.getTypeID(ped) == disabledPed:
                if ped not in disablePedArr:
                    disablePedArr.append(ped)
                if traci.trafficlight.getPhase(TLSID) != GREENSTATE_WE:
                    pedRedLight += 1

    for edge in crossings_NS:
        peds = traci.edge.getLastStepPersonIDs(edge)

        for ped in peds:
            if traci.person.getTypeID(ped) == disabledPed:
                if ped not in disablePedArr:
                    disablePedArr.append(ped)
                if traci.trafficlight.getPhase(TLSID) != GREENSTATE_NS:
                    pedRedLight += 1

    return pedRedLight

def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# Set logic for first traffic light
def setTlS1Logic(currState, logictls1, timeWE, timeNS):

    if logictls1 == 0:
        # First light without left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "grrrrrGggggggGGGGr", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "grrrrrGggggggGGrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrggggrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrryyyyrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "gGGGrrrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "gGGGrrrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "gGGGrrrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrrrrrrrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID, logic)
    else:
        # First light with left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "grrrrrGggggggGGGGr", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "grrrrrGggggggGGrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrggggrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrryyyyrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "gGGGrrrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "gGGGyyrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "gGGGGGrrrrrrrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyyyrrrrrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID, logic)


# Set logic for second traffic light
def setTlS2Logic(currState, logictls2, timeWE, timeNS):

    if logictls2 == 0:
        # Second light without left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "gGGgrrrrrGgggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "gGGgrrrrrGgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrryyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrryyyrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "rrrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrgGGGrrrrrrrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "rrrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrryyyyrrryyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrrrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrrrgggrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID2, logic)
    else:
        # Second light with left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "gGGgrrrrrGgggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "gGGgrrrrrGgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrryyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrryyyyyggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "rrrgGGGGGrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrgGGGyyrrrrrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "rrrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrryyyyrrryyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrrrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrrrgggrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID2, logic)


def saveResults():
    with open("Results/simulation3_2_parallel.txt", "a") as file:
        print("waitingTimes = " + str(bestWaitingTimes), file=file)
        print("cycleTimes = " + str(bestCycleTimes), file=file)
        print("stdeviation = " + str(bestStdeviation), file=file)
        print("----" * 80, file=file)


# this is the main entry point of this script
if __name__ == "__main__":
    # load whether to run with or without GUI
    options = get_options()
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # Sumo binary just sumo to not run GUI
    sumoBinary = checkBinary('sumo')

    # Hillclimb algorithm

    # Variables for hillclimber
    bestWaitingTimes = []  # Hillclimber output array // Optimilized value
    bestCycleTimes = []
    bestStdeviation = []
    target = False
    # Min and max value of green phase time length
    # Bottom limit needs to allow regular pedestrians to cross road safely (45m for 1.2m/s speed ~38s)
    limits = [160, 240]
    step_size = 32

    parallelNumber = 10 #How many times we want to look for candidate random value
    greentimeWE, greentimeNS = 0, 0

    simulations = 0
    count = 0

    # Demand directory
    demandDir = 'network/networkGenerations/demand_12_13/config_12_13'

    # First step of the simulation
    step = int(np.around(limits[0] + rand(1) * (limits[1] - limits[0])))
    # step = 196
    step = step - 33
    greentimeWE = round(step * 0.375)-10 #43
    greentimeNS = round(step * 0.625)-18 #57
    traci.start([sumoBinary, '-c', os.path.join(demandDir, f'run_config_{random.randint(0,19)}.sumocfg')])
    wtime, stdev = run()
    bestWaitingTimes.append(wtime)
    bestCycleTimes.append(step+33)
    bestStdeviation.append(stdev)
    waitingTime=wtime

    while not target:

        candidateList = []
        candidateWaitingTime = []
        candidatestdeviation = []

        for i in range(0, parallelNumber+1):
            candidate = int(np.around(step + randn(1) * step_size))
            candidate = max(candidate, limits[0])
            candidate = min(candidate, limits[1])
            candidateList.append(candidate)
            candidate = candidate - 33
            greentimeWE = round(candidate*0.375)-10
            greentimeNS = round(candidate*0.625)-18
            wtimearr = []
            stdevarr = []
            traci.start([sumoBinary, '-c', os.path.join(demandDir, f'run_config_{random.randint(0,19)}.sumocfg')])
            wtime, stdev = run()
            candidateWaitingTime.append(wtime)
            candidatestdeviation.append(stdev)
            print("Candidate: " + str(candidateList[-1]) + "// waiting time: " + str(wtime))

        for i in range(len(candidateWaitingTime)):

            if candidateWaitingTime[i] <= waitingTime:
                if candidateList[i] != step:
                    count = 0
                else:
                    count += 1
                step, waitingTime = candidateList[i], candidateWaitingTime[i]
                bestWaitingTimes.append(waitingTime)
                bestCycleTimes.append(step)
                bestStdeviation.append(candidatestdeviation[i])
            else:
                count += 1

            simulations += 1

        if count >= 10:
            count = 0
            step_size = step_size / 2

        if simulations > 150 or step_size < 1:
            target = True

    print(bestWaitingTimes)
    print(bestCycleTimes)
    print(bestStdeviation)
    plotWaitingTimes(bestWaitingTimes, bestCycleTimes, bestStdeviation)
