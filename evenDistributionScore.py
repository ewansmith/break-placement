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
    38875,  # below 25.55 minutes -> 1
    49625,  # below 33.05 minutes -> 2
    73875,  # below 49.15 minutes -> 3
    95125,  # below 63.25 minutes -> 4
    115625,  # below 77.05 minutes -> 5
    136625,  # below 91.05 minutes -> 6
    157625,  # below 105.05 minutes -> 7
    178625,  # below 119.05 minutes -> 8
    184625,  # below 123.05 minutes -> 9
    205625,  # below 137.05 minutes -> 10
]
breakLookup.sort()  # ensure sorted for bisect


def getLength(prodNo="1_7133_0001.004"):
    """
    Get length of content from API using production number
    """
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    keyInfo = json['_embedded']['programmeVersions'][0]['partTimes'][0]
    start = keyInfo['som'].split(':')
    end = keyInfo['eom'].split(':')
    start = '10:00:00:00'.split(':')
    end = '11:25:40:21'.split(':')
    som = [int(x) for x in start]
    eom = [int(x) for x in end]
    difference = np.subtract(eom, som)

    return (difference[0] * 3600 * 25) + (difference[1] * 60 * 25) + (difference[2] * 25) + difference[3]


def breakPattern(length):
    """
    Return time series with placement score for each frame
    """
    breakNo = bisect.bisect_right(breakLookup, length) + 1  # get number of breaks required
    fiveMins = (5 * 60 * 25)  # five minutes of frames
    splits = length / (2 * (breakNo + 1))  # number of frames in each split
    inflectionPoints = [x * splits for x in range(2, 2 * (breakNo + 1))]
    score = np.zeros(fiveMins)  # initialise five minutes of zero score

    for i, point in enumerate(inflectionPoints):
        if i == len(inflectionPoints) - 1:  # go to zero for last 5 minutes
            endpoint = 0
            num = int(length - fiveMins - len(score))
        else:
            endpoint = 40 if score[-1] == 100 else 100
            num = int(point - len(score))

        section = np.linspace(int(score[-1]), endpoint, num)
        score = np.concatenate((score, section))

    score = np.concatenate((score, np.zeros(fiveMins)))  # add final 5 minutes of zero score

    return score

#Plot distibution to visualise
x = np.linspace(0, getLength(), getLength())
plt.plot(x, breakPattern(getLength()))
plt.show()

# Timecode plot
maxTimes = [12.29, 25.55, 33.05, 49.15, 63.25, 77.05, 91.05, 105.05, 119.0, 123.05, 137.05]

def getPrefNoBreakpoints(length):  # assuming continuous programme
    """
    Return the preferred number of breakpoints from the length in minutes
    """
    length = float(length)
    if length >= 137.05:
        difference = length - 137.05
        extra = difference // 14
        return int(10 + extra)

    else:
        for i in range(0, len(maxTimes)):
            if maxTimes[i] > length:
                return i


def roundTime(x, base=5):
    '''
    Return x rounded to 5
    '''
    return base * round(x / base)


def getMidpoint(start, end):
    '''
    Return the integer exactly halfway between start and end
    '''
    return (start + end) / 2


def timecodeToInt(timecode):
    '''
    Return timecode in seconds
    Used in getBreakpoints function
    '''
    temp = timecode.split(':')
    answer = [int(x) for x in temp]

    hours = (answer[0]-10) * (3600 * 25)
    mins =answer[1] * 60 * 25
    secs  =(answer[2] * 25)
    return hours + mins + secs

def getRuntime(prodNo, json):
    '''
    Return runtime in minutes of a production number
    Uses ['durations']['runtime'] - different to getLength
    '''
    showLength =  json['_embedded']['programmeVersions'][0]['durations']['runTime']
    return showLength

# breakpoints = 2 dimensional array
# First index corresponds to number of breakpoints, second index contains the time of breakpoint in seconds
breakpoints = []
for i in range(0,10):
    breakpoints.append([])

def getBreakpoints(prodNo):
    """
    Get breakpoints of content from API using production number
    """
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()

    breakpointParts = json['_embedded']['programmeVersions'][0]['partTimes']
    showLength = getRuntime(prodNo, json)
    noBreakpoints = getPrefNoBreakpoints(showLength)

    for part in breakpointParts:
        if part['partNo'] != 0 and \
                part['typeDescription'] != "Optional Break Point (Soft Part)":  # ignore optional breakpoints
                breakpoints[noBreakpoints].append(roundTime(getMidpoint(timecodeToInt(part["som"]), timecodeToInt(part["eom"]))))

def count_elements(seq):
    """
    Tally elements from `seq' and return dictionary
    """
    dict = {}
    for i in seq:
        dict[i] = dict.get(i, 0) + 1
    return dict

prodNos = ["1_7133_0001.004", "1_9961_0137.001", "2_4259_0359.001", "10_2465_0175.001"]

def plotBreakpoints():
    """
    Get breakpoints for all production numbers and plot them on a graph for its number of breakpoints
    """
    for prodNo in prodNos:
        getBreakpoints(prodNo)

    #Plot graphs for each number of breakpoints
    for arr in breakpoints:
        if arr: #ignore arrays with no breakpoints
            noBreakpoints = breakpoints.index(arr)
            maxLength = list(maxTimes)[noBreakpoints]

            #make dictionary containing every "timecode"(conv. to seconds) and its frequency
            frequency_dict = count_elements(arr)


            plt.plot(list(frequency_dict.keys()), list(frequency_dict.values()))
            plt.xlabel("Time in seconds of a breakpoint")
            plt.ylabel("Frequency")
            plt.title(f"Frequency of breakpoints using {noBreakpoints} breakpoints")
            plt.show()

#Plot timecode breakpoints
plotBreakpoints()



