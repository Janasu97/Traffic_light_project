import numpy as np
import matplotlib.pyplot as plt


def plotWaitingTimes(waitingTimes, cycleTimes, stdeviation):
    plt.figure()
    plt.title("Mean waiting Times of Simulations")
    plt.xlabel("cycle Times")
    plt.ylabel("waiting Time")
    plt.grid(which="major", axis="both")
    plt.plot(np.arange(len(cycleTimes)), waitingTimes)
    plt.fill_between(np.arange(len(cycleTimes)), list(np.array(waitingTimes) - np.array(stdeviation)), list(np.array(waitingTimes) + np.array(stdeviation)), alpha=0.3)
    plt.xticks(np.arange(len(cycleTimes)), cycleTimes)
    plt.savefig("Plots/WaitingTimePlot.png")
    plt.show()


def plotWaitingTimeAndOffset(waitingTimes, cycleTimes, offsetTimes):
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.scatter(waitingTimes, offsetTimes, cycleTimes, c=offsetTimes, cmap='hsv')
    ax.set_xlabel('waitingTimes')
    ax.set_ylabel('offsetTimes')
    ax.set_zlabel('cycleTimes')
    ax.invert_xaxis()
    fig.show()


def plotWaitingTimeAndOffsetV2(waitingTimes, cycleTimes, offsetTimes, stdeviation):
    fig, ax1 = plt.subplots()
    
    plt.title("Mean waiting Times of Simulations")
    ax1.set_xlabel("cycle Times")
    ax1.set_ylabel("waiting Time", color='b')
    ax1.grid(which="major", axis="both")
    ax1.plot(np.arange(len(cycleTimes)), waitingTimes)
    ax1.fill_between(np.arange(len(cycleTimes)), list(np.array(waitingTimes) - np.array(stdeviation)), list(np.array(waitingTimes) + np.array(stdeviation)), alpha=0.3)
    ax1.set_xticks(np.arange(len(cycleTimes)), cycleTimes)
    
    ax2 = ax1.twinx()
    ax2.plot(np.arange(len(cycleTimes)), offsetTimes, 'r*')
    ax2.set_ylabel('offset Times', color='r')
    
    plt.savefig("Plots/WaitingTimePlotOffset.png")
    plt.show()


def plotWaitingTimeAndOffsetV3(waitingTimes, cycleTimes, offsetTimes, offsetTimes2, stdeviation):
    fig, ax1 = plt.subplots()
    
    plt.title("Mean waiting Times of Simulations")
    ax1.set_xlabel("cycle Times")
    ax1.set_ylabel("waiting Time", color='b')
    ax1.grid(which="major", axis="both")
    ax1.plot(np.arange(len(cycleTimes)), waitingTimes)
    ax1.fill_between(np.arange(len(cycleTimes)), list(np.array(waitingTimes) - np.array(stdeviation)), list(np.array(waitingTimes) + np.array(stdeviation)), alpha=0.3)
    ax1.set_xticks(np.arange(len(cycleTimes)), cycleTimes)
    
    ax2 = ax1.twinx()
    ax2.plot(np.arange(len(cycleTimes)), offsetTimes, 'r*')
    ax2.plot(np.arange(len(cycleTimes)), offsetTimes2, 'g*')
    ax2.set_ylabel('offset Times', color='r')
    
    plt.savefig("Plots/WaitingTimePlotOffset.png")
    plt.show()


if __name__ == "__main__":
    waitingTimes = [26.354166666666668, 24.053571428571427, 23.882608695652173, 21.533333333333335, 19.35573122529644, 19.14761904761905, 18.23913043478261, 19.244765887113413, 19.078138998682476]
    cycleTimes = [85, 74, 40, 65, 59, 55, 60, 58, 61]
    # offsetTimes = [86, 19, 19, 24, 24, 24, 24, 24]
    stdeviation = [0] * 7 + [11.4, 11.6]
    # plotWaitingTimeAndOffsetV2(waitingTimes, cycleTimes, offsetTimes, stdeviation)
    plotWaitingTimes(waitingTimes, cycleTimes, stdeviation)
