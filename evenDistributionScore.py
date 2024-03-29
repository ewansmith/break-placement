import numpy as np
import matplotlib.pyplot as plt
import bisect
import requests


"""
Generates scores for content based on programme length
This is first fetched from Programme Version API using production number
Then the score is generated
"""

breakLookup = [
    38875, # below 25.55 minutes -> 1
    49625, # below 33.05 minutes -> 2
    73875, # below 49.15 minutes -> 3
    95125, # below 63.25 minutes -> 4
    115625, # below 77.05 minutes -> 5
    136625, # below 91.05 minutes -> 6
    157625, # below 105.05 minutes -> 7
    178625, # below 119.05 minutes -> 8
    184625, # below 123.05 minutes -> 9
    205625, # below 137.05 minutes -> 10
]
breakLookup.sort() # ensure sorted for bisect

def breakPattern(length):
    """
    Return time series with placement score for each frame
    """
    breakNo = bisect.bisect_right(breakLookup, length) + 1 # get number of breaks required
    fiveMins = (5 * 60 * 25) # five minutes of frames
    splits = length / (2 * (breakNo + 1)) # number of frames in each split
    inflectionPoints = [x * splits for x in range(2, 2 * (breakNo + 1))]
    score = np.zeros(fiveMins) # initialise five minutes of zero score

    for i, point in enumerate(inflectionPoints):
        if i == len(inflectionPoints) - 1: # go to zero for last 5 minutes
            endpoint = 0
            num = int(length - fiveMins - len(score))
        else:
            endpoint = 25 if score[-1] == 100 else 100
            num = int(point - len(score))

        section = np.linspace(int(score[-1]), endpoint, num)
        score = np.concatenate((score, section))

    score = np.concatenate((score, np.zeros(fiveMins))) # add final 5 minutes of zero score

    return score


# Plot distibution to visualise
# x=np.linspace(0, 60000, 60000)
# plt.plot(x, breakPattern(60000))
# plt.xlabel('Framecount')
# plt.ylabel('Score')
# plt.show()
