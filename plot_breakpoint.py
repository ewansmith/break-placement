import numpy as np
import matplotlib.pyplot as plt
import bisect
import requests
import json
from os.path import exists
from os import path
import utilities

"""
Plots separate graphs of frequency against (rounded) breakpoint timecode.
"""


def getBreakpoints(prodNo, breakpoints, count):
    """
    Get breakpoints of content from API using production number
    """
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    print(prodNo)
    if '_embedded' in json:
        breakpointParts = json['_embedded']['programmeVersions'][0]['partTimes']
        if breakpointParts:
            contentLength = utilities.timecodeToFrames(breakpointParts[0]["eom"]) - utilities.timecodeToFrames(
                breakpointParts[0]["som"])
            noBreakpoints = len(breakpointParts) - 1
            print("contentLength " + str(contentLength))
            print("noBreakpoints " + str(noBreakpoints))
            if contentLength != 0 and noBreakpoints != 0:
                count += 1
                for part in breakpointParts:
                    if part['partNo'] != 0 and \
                            part[
                                'typeDescription'] != "Optional Break Point (Soft Part)":  # ignore optional breakpoints
                        timecode = utilities.getMidpoint(utilities.timecodeToFrames(part["som"]),
                                                                             utilities.timecodeToFrames(part["eom"]))
                        print("bp: " + str(timecode) + " / " + str(contentLength))
                        breakpoints[noBreakpoints].append(utilities.roundTime(timecode / contentLength))
            else:
                print("0 content length")
        else:
            print("no parts")
    else:
        print("empty")
    return count


def getProdNos(json_file):
    """
    Return arrays of production numbers and their slot lengths found from api_results.json
    """
    # prodNos = ["1_7133_0001.004", "1_9961_0137.001", "2_4259_0359.001", "10_2465_0175.001"]
    prodNos = []
    slotLengths = []
    # Opening JSON file
    f = open(json_file)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Iterating through the json
    # list
    for entry in data['data']['entries']:
        prodNos.append(utilities.convertProdNo(entry['historicalId']))  # change formatting
        slotLengths.append(entry['parent']['intendedSlotLength'])

    # Closing file
    f.close()

    return prodNos, slotLengths


def storeBreakpoints(json_file):
    count = 0

    # initialise 2D breakpoints array
    # First index corresponds to number of breakpoints, second index contains the time of breakpoint in seconds
    breakpoints = []
    for i in range(0, 15):
        breakpoints.append([])

    # get production numbers and slot lengths
    # for each one, call getBreakpoints
    prodNos, slotLengths = getProdNos(json_file)
    for j in range(0, len(prodNos)):
        prodNo = prodNos[j]
        slotLength = slotLengths[j]
        count = getBreakpoints(prodNo, breakpoints, count)
    print("successful prod id's : " + str(count))

    for i in range(0, len(breakpoints)):
        if breakpoints[i]:
            count_dict = utilities.count_elements(breakpoints[i])
            f = open("breakpoint%s.json" % i, 'w')
            f.truncate()
            json.dump(count_dict, f)
            f.close()

def plotBreakpoints(i):
    """
    Get breakpoints from file and plot them on a graph
    (for specified range of content length)
    """
    f = open("breakpoint%s.json" % i)
    count_dict = json.load(f)
    print(count_dict)
    plt.scatter(list(count_dict.keys()), list(count_dict.values()))
    plt.xlabel("Time in seconds of a breakpoint")
    plt.ylabel("Frequency")
    plt.title(f"Frequency of breakpoints using {i} breakpoints")
    plt.show()
    f.close()


# Plot timecode breakpoints
# storeBreakpoints('api_results.json')
for i in range(1, 15):
    if exists("breakpoint%s.json" % i):
        plotBreakpoints(i)
