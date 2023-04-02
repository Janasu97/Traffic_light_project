import xml.etree.ElementTree as ET
import statistics
from xml.dom import minidom

def getXMLValues(path):
    tripInfo = ET.parse(path)
    tripInfoRoot = tripInfo.getroot()

    childrenVeh = []
    childrenPed = []
    sortedChildren = []

    for child in tripInfoRoot:
        if child.tag == "tripinfo":
            childrenVeh.append(child)
        elif child.tag == "personinfo":
            childrenPed.append(child)

    return childrenVeh, childrenPed

def waitingTimeCalc(sortedChildren):
    waitingtimes = []

    for child in sortedChildren:
        waitingtimes.append(float(child.get("waitingTime")))

    meanWaitingTime = sum(waitingtimes)/len(waitingtimes)
    return meanWaitingTime

def cntVeh(sortedChildren):
    vehCnt = 0
    for child in sortedChildren:
        vehCnt+=1

    return vehCnt

def stdDevCalc(sortedChildren):
    waitingtimes = []

    for child in sortedChildren:
        waitingtimes.append(float(child.get("waitingTime")))

    stdeviation = statistics.stdev(waitingtimes)
    return stdeviation


def cntPed(sortedChildren):
    disPedCnt = 0
    normalPedCnt = 0
    for child in sortedChildren:
        if child.get("type") == "DEFAULT_PEDTYPE":
            normalPedCnt+=1
        else:
            disPedCnt+=1
    return normalPedCnt, disPedCnt

