import matplotlib.pyplot as plt
import numpy as np


x = np.array(["I", "II", "III", "IV", "V"])


# 7-8
# y1 = np.array([36.67, 35.79, 35.8, 55.64, 64.92])
# y2 = np.array([35.79, 37.21, 37.65, 74.87, 82.8])
# y3 = np.array([36.72, 38.32, 38.93, 94.31, 115.52])
# 12-13
# y1 = np.array([30.36, 31.89, 32.12, 40.9, 38.29])
# y2 = np.array([30.0, 32.44, 33.09, 43.12, 44.01])
# y3 = np.array([30.15, 34.05, 34.4, 55.51, 54.65])
# # 17-18
# y1 = np.array([98.43, 117.12, 119.64, 156.83, 152.07])
# y2 = np.array([105.97, 133.52, 131.27, 169.72, 172.16])
# y3 = np.array([99.07, 125.71, 126.99, 172.74, 168.76])
#
# Overall
y1 = np.array([55.15, 61.60, 62.52, 84.46, 85.09])
y2 = np.array([57.25, 67.72, 67.34, 95.90, 99.66])
y3 = np.array([55.31, 66.03, 66.77, 107.52, 112.98])
plt.plot(x, y1, label="Low (10%)")
plt.plot(x, y2, label="Medium (15%)")
plt.plot(x, y3, label="High (25%)")
plt.title("Mean waiting time of vehicles in all timeframes")
plt.xlabel("Algorithm used")
plt.ylabel("Mean waiting time of vehicles [s]")
plt.legend()
plt.show()
#
# y1 = np.array([0.98, 0.35, 0.34, 0.79, 0.48])
# y2 = np.array([1.00, 0.32, 0.32, 0.76, 0.37])
# y3 = np.array([1.02, 0.29, 0.28, 0.74, 0.35])
# plt.bar(x, y1, label="Low (10%)")
# plt.bar(x, y2, label="Medium (15%)")
# plt.bar(x, y3, label="High (25%)")
# plt.title("Special type pedestrians walking on red light")
# plt.xlabel("Algorithm used")
# plt.ylabel("Special type pedestrians walking on red light [s]")
# plt.legend()
# plt.show()