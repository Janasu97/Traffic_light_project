from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import optparse
import traci
from sumolib import checkBinary


# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


def run(label="sim0"):
    """execute the TraCI control loop"""
    conn = traci.getConnection(label)
    step = 0
    while conn.simulation.getMinExpectedNumber() > 0:
        conn.simulationStep()
        step += 1
    conn.close()
    traci.switch(label)
    traci.close()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=True, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


def main(configurationFile, tripinfoOutput=None, summaryOutput=None, fullOutput=None, label="sim0"):
    options = get_options()

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    if((tripinfoOutput is not None) and (summaryOutput is not None) and (fullOutput is not None)):
        traci.start([sumoBinary, "-c", configurationFile,
                     "--tripinfo-output", tripinfoOutput,
                     "--summary", summaryOutput,
                     "--full-output", fullOutput], label=label)
    elif ((tripinfoOutput is not None) and (summaryOutput is None) and (fullOutput is None)):
        traci.start([sumoBinary, "-c", configurationFile,
                        "--tripinfo-output", tripinfoOutput], label=label)
    else:
        traci.start([sumoBinary, "-c", configurationFile], label=label)
    
    run(label)
