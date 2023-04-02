#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import valueCalc
import numpy as np
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




# Green states in W-E and N-S directions
GREENSTATE_WE = 0
GREENSTATE_NS = 5

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
    # track the duration for which the green phase of the vehicles has been active
    tracicounter = 0
    countPhaseDiffToThree = 0
    pedRedLight = 0
    totalPedRedLight = 0
    greenTimeSoFarWE = 0
    greenTimeSoFarNS = 0
    tmToGoBackToCycle = 0
    holdTmToGoBackToCycle = 0
    noLeftTurnFlagOn = False

    # whether the pedestrian button has been pressed and if TLS logic changed already
    chngPhaseAnyway = False

    # Variables for switching off Left and Right turn green phases
    noGreenRightTurn, noGreenRightTurnNS, noGreenLeftTurn = False, False, False

    totalWaitNPed = 0
    totalWaitDisPed = 0
    #Induction loop
    loopNS = False
    loopSN = False

    # Just to test cycle time
    flagNewPhase = False
    totCycleTimeCounter = 1 #So first cycle is counted properly
    cycleTimearray = []
    cycleCounter = 0

    # main loop. do something every simulation step until no more vehicles are
    # loaded or running
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        tracicounter += 1

        # Checking of the Cycle time consistency so this traffic light will be compatible in city system (green wave)
        if traci.trafficlight.getPhase(TLSID) == 1:
            flagNewPhase = True

        if traci.trafficlight.getPhase(TLSID) == 0 and flagNewPhase == True:
            flagNewPhase = False
            cycleCounter += 1 #Number of cycles in simulation
            cycleTimearray.append(totCycleTimeCounter)
            totCycleTimeCounter = 0

        totCycleTimeCounter += 1

        # To secure that program is running algorithm set by user
        if tracicounter == 1:
            setTlS1Logic(0, 0, greentimeWE, greentimeNS, False, False)
            setTlS2Logic(0, 0, greentimeWE, greentimeNS, False, False)

        #  To make sure we change the algorithm back to normal after special no lef turn logic
        if noLeftTurnFlagOn and basicSpecialPed and traci.trafficlight.getPhase(TLSID) == 1:
            setTlS1Logic(1, 0, greentimeWE, greentimeNS, noGreenRightTurn, noGreenRightTurnNS)
            setTlS2Logic(1, 0, greentimeWE, greentimeNS, noGreenRightTurn, noGreenRightTurnNS)
            noLeftTurnFlagOn = False

        # Count total time spent by disabled pedestrians on crossing during red phase
        totalPedRedLight += calcredlightped(CROSSINGS_WE, CROSSINGS_NS, pedRedLight=0)


        # Count total waiting time for both times of pedestrians
        tWNP_WE, tWDP_WE = calcPedMeanWaitingTimes(WALKINGAREAS_WE, CROSSINGS_WE)
        tWNP_NS, tWDP_NS = calcPedMeanWaitingTimes(WALKINGAREAS_NS, CROSSINGS_NS)

        totalWaitNPed += tWNP_WE + tWNP_NS
        totalWaitDisPed += tWDP_WE + tWDP_NS

        # Special functionality locked with flag in properties
        if basicSpecialPed:
            # Special functionality for WE direction
            if traci.trafficlight.getPhase(TLSID) == GREENSTATE_NS:
                greenTimeSoFarNS += 1
                if greenTimeSoFarNS >= MIN_GREEN_TIME_NS:
                    # check whether someone has pushed the button
                    activeRequest_WE = checkWaitingPersons(WALKINGAREAS_WE, CROSSINGS_WE)
                    if activeRequest_WE:
                        # switch to the next phase
                        # If less than 3 it would cause a problem with switching yellow phase
                        if tmToGoBackToCycle == 0:
                            if greentimeNS-greenTimeSoFarNS > 3 or chngPhaseAnyway:
                                if countPhaseDiffToThree == 0:
                                    traci.trafficlight.setPhase(TLSID2, traci.trafficlight.getPhase(TLSID2)+1)
                                    chngPhaseAnyway = True
                                countPhaseDiffToThree += 1
                                if countPhaseDiffToThree > 3:
                                    traci.trafficlight.setPhase(TLSID, GREENSTATE_NS + 1)
                                    countPhaseDiffToThree = 0
                                    # activeRequest_WE = False
                                    tmToGoBackToCycle = greentimeNS - greenTimeSoFarNS - (longerGreenTimeWE-greentimeWE)
                                    greenTimeSoFarNS = 0
                                    chngPhaseAnyway = False
                        else:
                            tmToGoBackToCycle = longerGreenTimeWE-greentimeWE
                    elif greenTimeSoFarNS == greentimeNS+tmToGoBackToCycle: #No request for the whole duration of green
                        tmToGoBackToCycle = 0
            else:
                greenTimeSoFarNS = 0

            # At the last phase try to bring  the control algorithm to initial state if there is no trigger
            # from detected special needs pedestrian or cars in N-S direction trying to turn left
            if traci.trafficlight.getPhase(TLSID) == 9:
                activeRequest_WE = checkWaitingPersons(WALKINGAREAS_WE, CROSSINGS_WE)
                if activeRequest_WE == True:
                    loopSN, loopNS = False, False  # To prevent induction loop from changing phase length
                    TLSLogicFlagLongerWE = True
                    if noRightTurn:
                        noGreenRightTurn = True
                    if noLeftTurn:
                        setTlS1Logic(9, 2, longerGreenTimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                        setTlS2Logic(9, 2, longerGreenTimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                        noLeftTurnFlagOn = True
                    else:
                        setTlS1Logic(9, 0, longerGreenTimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                        setTlS2Logic(9, 0, longerGreenTimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                elif activeRequest_WE == False:
                    # To make it back to normally working algorithm with normal green phase lengths
                    TLSLogicFlagLongerWE = False
                    noGreenRightTurn = False
                    setTlS1Logic(9, 0, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                    setTlS2Logic(9, 0, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)


            if noRightTurn:
                # Special functionality for NS direction
                if traci.trafficlight.getPhase(TLSID) == 2: #Right before switching on green for NS direction
                    # check whether someone has pushed the button
                    activeRequest_NS = checkWaitingPersons(WALKINGAREAS_NS, CROSSINGS_NS)
                    if activeRequest_NS:
                        noGreenRightTurnNS = True
                    else:
                        noGreenRightTurnNS = False
                if traci.trafficlight.getPhase(TLSID) == 4: #Right before switching on green for NS direction
                    # check whether someone has pushed the button
                    activeRequest_NS = checkWaitingPersons(WALKINGAREAS_NS, CROSSINGS_NS)
                    if activeRequest_NS:
                        noGreenRightTurnNS = True
                    else:
                        noGreenRightTurnNS = False

                    setTlS1Logic(4, 0, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
        # End of special functionality

        # Induction loop functionality
        # Check for the cars trying to turn left in N-S direction
        if traci.trafficlight.getPhase(TLSID2) == 0 and loopSN == True:
            loopSN = False
            setTlS2Logic(0, 0, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)

        if traci.trafficlight.getPhase(TLSID) == 0 and loopNS == True:
            loopNS = False
            setTlS1Logic(0, 0, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)

        if loopNS == False:
            if traci.trafficlight.getPhase(TLSID) == 5:
                trigLoopNS = traci.inductionloop.getLastStepVehicleNumber('loop_N_S')
                if trigLoopNS != 0:
                    setTlS1Logic(5, 1, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                    loopNS = True

        if loopSN == False:
            if traci.trafficlight.getPhase(TLSID2) == 2:
                trigLoopSN = traci.inductionloop.getLastStepVehicleNumber('loop_S_N')
                if trigLoopSN != 0:
                    setTlS2Logic(2, 1, greentimeWE, greentimeNS+tmToGoBackToCycle, noGreenRightTurn, noGreenRightTurnNS)
                    loopSN = True

    # End of the simulation
    sys.stdout.flush()
    traci.close()


    # Gather the results
    meanWaitingTimeList = []
    stdeviationList = []
    childrenVeh, childrenPed = valueCalc.getXMLValues(tripinfoOutput)

    meanWaitingTime = valueCalc.waitingTimeCalc(childrenVeh)
    vehCnt = valueCalc.cntVeh(childrenVeh)
    meanWaitingTimeList.append(meanWaitingTime)
    stdeviation = valueCalc.stdDevCalc(childrenVeh)
    stdeviationList.append(stdeviation)
    std = math.sqrt(sum(np.power(stdeviationList, 2)) / len(stdeviationList))

    normalPedCnt, disPedCnt = valueCalc.cntPed(childrenPed)
    return meanWaitingTime, std, vehCnt, totalWaitNPed/normalPedCnt, normalPedCnt, totalWaitDisPed/disPedCnt, disPedCnt, totalPedRedLight/disPedCnt


# Detect the special needs pedestrians awaiting green phase to cross the street
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

# Calculate the amount of time the special need pedestrians are spending on the red light
# while walking over pedestrian crossing
def calcredlightped(crossings_WE, crossings_NS, pedRedLight):
    # Check for the pedestrians currently on the crossings
    for edge in crossings_WE:
        peds = traci.edge.getLastStepPersonIDs(edge)

        for ped in peds:

            if traci.person.getTypeID(ped) == disabledPed:
                if ped not in disablePedArr:
                    disablePedArr.append(ped)
                numOfPhase = traci.trafficlight.getPhase(TLSID)
                if numOfPhase != GREENSTATE_WE and numOfPhase != 10 and numOfPhase != 11:
                    pedRedLight += 1

    # For NS direction we need to do separate calculation as green pedestrian phase is in different cycle part
    peds = traci.edge.getLastStepPersonIDs(crossings_NS[0])

    for ped in peds:
        if traci.person.getTypeID(ped) == disabledPed:
            if ped not in disablePedArr:
                disablePedArr.append(ped)
            if traci.trafficlight.getPhase(TLSID) != 5 and traci.trafficlight.getPhase(TLSID) != 6 \
                    and traci.trafficlight.getPhase(TLSID) != 7:
                pedRedLight += 1

    peds = traci.edge.getLastStepPersonIDs(crossings_NS[1])

    for ped in peds:
        if traci.person.getTypeID(ped) == disabledPed:
            if ped not in disablePedArr:
                disablePedArr.append(ped)
            if traci.trafficlight.getPhase(TLSID2) != 4 and traci.trafficlight.getPhase(TLSID2) != 5 \
                    and traci.trafficlight.getPhase(TLSID2) != 6:
                pedRedLight += 1

    return pedRedLight



# Calculate the mean waiting times of pedestrians in the simulation. For both normal and special needs pedestrians
def calcPedMeanWaitingTimes(walkingAreas, crossings):
    waitDisPed = 0
    waitNormalPed = 0
    for edge in walkingAreas:
        peds = traci.edge.getLastStepPersonIDs(edge)
        for ped in peds:

            if (traci.person.getSpeed(ped) < 1 and traci.person.getNextEdge(ped) in crossings):
                if traci.person.getTypeID(ped) == disabledPed:
                    waitDisPed += 1
                else:
                    waitNormalPed += 1

    return waitNormalPed, waitDisPed


def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# Setting the traffic light control logic for the first traffic lights.
def setTlS1Logic(currState, logictls1, timeWE, timeNS, noGreenRightTurnWE, noGreenRightTurnNS):

    if noGreenRightTurnNS == True:
        greenRed = "r"
    else:
        greenRed = "g"

    if logictls1 == 0:
        # First light without left turn

        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  greenRed + "rrrrrGggggggGGGGr", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "grrrrrGggggggGGrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrggggrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrryyyyrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrrrrrrrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID, logic)
    elif logictls1 == 1:
        # First light with left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "grrrrrGggggggGGGGr", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "grrrrrGggggggGGrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrggggrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyrryyyyrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "gGGGyyrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  "gGGGGGrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyyyyrrrrrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrrrryyyyyyyyyrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID, logic)
    elif logictls1 == 2:
        # Special logic to prevent left turning cars hit pedestrians on crossing
        phases = []
        phases.append(traci.trafficlight.Phase((timeWE/2)-10, greenRed + "rrrrrGggggggGGGGr", 0, 0))  # half time - 10 s
        phases.append(traci.trafficlight.Phase(10, "grrrrrGggggggGGrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21, "rrrrrrggggrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "yyyyrryyyyrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS, "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(15, "gGGGrrrrrr" + greenRed + "rrrrrrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "yyyyrrrrrrrrrrrrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "rrrrrryyyyyyyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase((timeWE/2-3), greenRed + "rrrrrrgggrggrrGGr", 0, 0))  # half time - 10 s -3s
        phases.append(traci.trafficlight.Phase(3, greenRed + "rrrrrygggrggyyGGr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID, logic)


# Setting the traffic light control logic for the second traffic lights.
def setTlS2Logic(currState, logictls2, timeWE, timeNS, noGreenRightTurnWE, noGreenRightTurnNS):

    if noGreenRightTurnNS == True:
        greenRed = "r"
    else:
        greenRed = "g"


    if logictls2 == 0:
        # Second light without left turn

        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "gGG" + greenRed + "rrrrrGgggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "gGGgrrrrrGgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrryyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrryyyrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  greenRed + "rrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   greenRed + "rrgGGGrrrrrrrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  greenRed + "rrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrryyyyrrryyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrrrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrrrgggrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID2, logic)
    elif logictls2 == 1:
        # Second light with left turn
        phases = []
        phases.append(traci.trafficlight.Phase(timeWE,  "gGGgrrrrrGgggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "gGGgrrrrrGgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrryyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrryyyyyggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  greenRed + "rrgGGGGGrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   greenRed + "rrgGGGyyrrrrrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  greenRed + "rrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrryyyyrrryyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrrrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrrrgggrrr", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID2, logic)
    elif logictls2 == 2:
        # Special logic to prevent left turning cars hit pedestrians on crossing
        phases = []
        phases.append(traci.trafficlight.Phase((timeWE/2)-10,  "gGG" + greenRed + "rrrrrGgggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(10,  "gGGgrrrrrGgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrryyyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrrryyyrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(15,  greenRed + "rrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   greenRed + "rrgGGGrrrrrrrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(timeNS,  greenRed + "rrgGGGrrrgggrGr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "rrryyyyrrryyyrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(21,  "rrrrrrrrrggggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase(3,   "yyyrrrrrrrgggrrr", 0, 0))
        phases.append(traci.trafficlight.Phase((timeWE/2)-3, "rrr" + greenRed + "rrrrrygggGrG", 0, 0))
        phases.append(traci.trafficlight.Phase(3, "ryy" + greenRed + "rrrrrrgggGrG", 0, 0))
        logic = traci.trafficlight.Logic("0", 0, currState, phases)
        traci.trafficlight.setCompleteRedYellowGreenDefinition(TLSID2, logic)


# Saving the results in the txt file
def saveResults():
    with open("network/statistics/simulation_output.txt", "a") as file:
        print(f"Simualtion conditions: {basicSpecialPed}, {noRightTurn}, {noLeftTurn}, {demandSpecPed}, {demandDir}", file=file)
        print("Total mean waiting times of cars: " + str(round(sum(WaitingTimesVehicles)/simulations,2)), file=file)
        print("Total standard deviation: " + str(round(sum(bestStdeviation)/simulations,2)), file=file)
        print("Total mean waiting times of normal pedestrians: " + str(round(sum(waitingTimesPedN)/simulations,2)), file=file)
        print("Total mean waiting times of special pedestrians: " + str(round(sum(waitingTimesPedD)/simulations,2)), file=file)
        print("Red light disabled pedestrians red light on: " + str(round(sum(totalDPedRedTime)/simulations,2)), file=file)
        print("Total mean amount of regular pedestrians: " + str(sum(totalAmountPedN)/simulations), file=file)
        print("Total mean amount of disabled pedestrians: " + str(sum(totalAmountPedD)/simulations), file=file)
        print("----" * 80, file=file)


# this is the main entry point of this script
if __name__ == "__main__":
    # load whether to run with or without GUI
    options = get_options()
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # Here you decide if you want to see the simulation running in SUMO-GUI. To not see the
    # simulation run just uncommment the line below.
    sumoBinary = checkBinary('sumo')

    # Select the percentage of special needs pedestrians among all of the pedestrians.
    disPedPercArray = ["L", "M", "H"]
    for demandPerc in disPedPercArray:
        # !!! Very important point. Here you select the special simulation properties !!!
        basicSpecialPed = True
        noRightTurn = True
        noLeftTurn  = True

        # Demand directory
        demandDir = 'network/networkGenerations/demand_7_8_special/config_7_8'
        demandSpecPed = demandPerc #Low // Medium // High percentage of special needs pedestrians among pedestrians

        # Special simulation variables
        noGreenRightTurn = True
        noGreenLeftTurn = True
        baseSpecialPed = True

        # Output variables
        WaitingTimesVehicles = []
        bestStdeviation = []
        waitingTimesPedN = []
        waitingTimesPedD = []
        totalDPedRedTime = []
        totalAmountVehicles = []
        totalAmountPedN = []
        totalAmountPedD = []
        target = False

        greentimeWE, greentimeNS = 0, 0
        simulations = 20     #Number of simulations
        count = 0


        for simnr in range(simulations):
            # Set values for the green phase ratio
            greentimeWE = int(137 * 0.35) - 10
            greentimeNS = int(137 * 0.65) - 18
            # greentimeWE = 38
            # greentimeNS = 61
            longerGreenTimeWE = 60

            # minimum green time for the vehicles in NS direction
            MIN_GREEN_TIME_NS = greentimeNS-(longerGreenTimeWE-greentimeWE)

            print(simnr)
            traci.start([sumoBinary, '-c', os.path.join(demandDir, f'run_config_{demandSpecPed}_{simnr}.sumocfg')])
            wtime, stdev, vehCnt, totalWaitNPed, normalPedCnt, totalWaitDisPed, disPedCnt, totalPedRedLight = run()


            # Append the results from each simulation
            WaitingTimesVehicles.append(wtime)
            bestStdeviation.append(stdev)
            totalAmountVehicles.append(vehCnt)
            waitingTimesPedN.append(totalWaitNPed)
            totalAmountPedN.append(normalPedCnt)
            waitingTimesPedD.append(totalWaitDisPed)
            totalAmountPedD.append(disPedCnt)
            totalDPedRedTime.append(totalPedRedLight)


        # In case you want to see the results printed in the console
        # printVar = 0
        # if printVar == 1:
        #     print("Mean waiting times of cars: ")
        #     print(*WaitingTimesVehicles, sep=",")
        #
        #     print("Standard deviation: ")
        #     print(*bestStdeviation, sep=",")
        #
        #     print("Mean waiting times of normal pedestrians: ")
        #     print(*waitingTimesPedN, sep=",")
        #
        #     print("Mean waiting times of special pedestrians: ")
        #     print(*waitingTimesPedD, sep=",")
        #
        #     print("Mean waiting times spent on crossing with red light on: ")
        #     print(*totalDPedRedTime, sep=",")
        # else:
        #     print("Total mean waiting times of cars: " + str(sum(WaitingTimesVehicles)/simulations))
        #     print("Total standard deviation: " + str(sum(bestStdeviation)/simulations))
        #     print("Total mean waiting times of normal pedestrians: " + str(sum(waitingTimesPedN)/simulations))
        #     print("Total mean waiting times of special pedestrians: " + str(sum(waitingTimesPedD)/simulations))
        #     print("Total mean waiting times spent on crossing with red light on: " + str(sum(totalDPedRedTime)/simulations))

        saveResults()

