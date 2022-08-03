import matplotlib.pyplot as plt
import requests
import json
import os.path
from os import path
import utilities

"""
Plots separate graphs of frequency against (rounded) breakpoint timecode.
"""

max_breakpoints = 30


class Production:
    def __init__(self, ID: object, soe: object = None, som: object = None, eom: object = None,
                 optionalBreakpoints: object = [None],
                 preferredBreakpoints: object = [None]) -> object:
        self.ID = ID
        self.soe = soe
        self.som = som
        self.eom = eom
        self.optionalBreakpoints = optionalBreakpoints
        self.preferredBreakpoints = preferredBreakpoints

    def setTimecodes(self, a, b, c):
        self.soe = a
        self.som = b
        self.eom = c

    def addBreakpoint(self, som, eom, type):
        if type == "Optional Break Point (Soft Part)":
            self.optionalBreakpoints.append([som, eom])
        elif type == "Preferred Break Point (Soft Part)":
            self.preferredBreakpoints.append([som, eom])
        # print('added ' + type + " " + som + " " + eom)

    def clearBreakpoints(self):
        self.optionalBreakpoints.clear()
        self.preferredBreakpoints.clear()

    def getID(self):
        return self.ID


def storeProductionObj(production, write_file='productions.json'):
    """Given production object, stores it in write_file json"""
    if path.isfile(write_file) is False:
        raise Exception("File not found")
    # print(production.__dict__)
    wf = open(write_file)
    production_arr = json.load(wf)
    production_arr['data'].append(production.__dict__)
    with open(write_file, 'w') as json_file:
        json.dump(production_arr, json_file, indent=4, separators=(',', ': '))
    # print('Successfully appended to the JSON file')
    wf.close()


def getProdNos(read_file='api_results.json'):
    """
    Return arrays of production numbers and their slot lengths found from api_results.json
    """
    # prodNos = ["1_7133_0001.004", "1_9961_0137.001", "2_4259_0359.001", "10_2465_0175.001"]
    prodNos = []
    # Opening JSON file
    f = open(read_file)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Iterating through the json
    # list
    for entry in data['data']['entries']:
        prodNos.append(utilities.convertProdID(entry['historicalId']))  # change formatting

    # Closing file
    f.close()

    return prodNos


def appendJsonDict(relative_timecode, no_breakpoints):
    """
    Edit the counts stored in a dictionary json file.
    File name depends on no_breakpoints
    """
    dict_file = "%s_dict.json" % no_breakpoints
    # print("right file: " + str(dict_file))
    if os.path.exists(dict_file):
        f = open(dict_file, 'r')
        dict = json.load(f)
        f.close()
    else:
        dict = {}

    if relative_timecode not in dict.keys():
        dict[relative_timecode] = 1
    else:
        dict[relative_timecode] += 1

    f = open(dict_file, 'w')
    f.truncate()
    json.dump(dict, f)
    f.close()


def filterProductions(prodNo):
    """
    Get breakpoints of content from API using production number
    """
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    valid_breakpoints = False
    production = Production(prodNo)
    production.clearBreakpoints()
    print(prodNo)

    if '_embedded' not in json:
        return []

    breakpointParts = json['_embedded']['programmeVersions'][0]['partTimes']

    if breakpointParts == None or breakpointParts == [] or breakpointParts[0]['partNo'] != 0:
        return []

    noBreakpoints = len(breakpointParts) - 1

    soe = breakpointParts[0]['soe']
    som = breakpointParts[0]['som']  # start of production
    eom = breakpointParts[0]['eom']  # end of production

    if som == "           " or som is None or soe is None or eom is None:
        return []

    production.setTimecodes(soe, som, eom)
    startOfMessage = utilities.timecodeToFrames(som)
    endOfMessage = utilities.timecodeToFrames(eom)
    contentLength = endOfMessage - startOfMessage

    # print("contentLength " + str(contentLength))
    # print("noBreakpoints " + str(noBreakpoints))

    if contentLength == 0 and noBreakpoints == 0:
        return []

    for i in range(1, len(breakpointParts)):
        part = breakpointParts[i]
        type_x = part['typeDescription']

        bp_som = part['som']  # start of break
        bp_eom = part['eom']  # end of break
        if bp_som is None or bp_eom is None:
            return []

        if type_x == "Optional Break Point (Soft Part)" \
                or type_x == "Preferred Break Point (Soft Part)":
            timecode = utilities.getMidpoint(utilities.timecodeToFrames(bp_som),
                                             utilities.timecodeToFrames(bp_eom))
            relative_timecode = round((timecode / contentLength), 2)
            if relative_timecode > 1:
                print(prodNo)
                print(noBreakpoints)
                print("more than 1?!")
                print("timecode: " + str(timecode))
                print("contentLength: " + str(contentLength))
                print("relative_timecode: " + str(relative_timecode))
            appendJsonDict(str(relative_timecode), noBreakpoints)
            production.addBreakpoint(bp_som, bp_eom, type_x)
            valid_breakpoints = True

    if valid_breakpoints:
        storeProductionObj(production)


def getBreakpoints():
    """Get breakpoints from a list of production ID's"""
    # get production numbers and slot lengths
    # for each one, call getBreakpoints
    prodNos = getProdNos()
    for j in range(0, len(prodNos)):
        prodNo = prodNos[j]
        filterProductions(prodNo)

def extract_breakpoints(read_file="productions.json"):
    '''
    Extract breakpoints from json of production objects containing timecode strings
    '''
    # Opening JSON file
    f = open(read_file)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Iterating through the json
    # list
    for prod in data['data']:
        som = prod['som']
        eom = prod['eom']
        optionalBreakpoints = prod['optionalBreakpoints']
        preferredBreakpoints = prod['preferredBreakpoints']
        noBreakpoints = len(preferredBreakpoints) + len(optionalBreakpoints)
        startOfMessage = utilities.timecodeToFrames(som)
        endOfMessage = utilities.timecodeToFrames(eom)
        contentLength = endOfMessage - startOfMessage
        for obp in optionalBreakpoints:
            bp_start = utilities.timecodeToFrames(obp[0])
            bp_end = utilities.timecodeToFrames(obp[1])
            timecode = utilities.getMidpoint(bp_start, bp_end)
            relative_timecode = utilities.roundPartial(timecode / contentLength, 0.02)
            if relative_timecode >= 1:
                print("Bigger than 1")
                print(timecode)
                print(contentLength)
            appendJsonDict(str(relative_timecode), noBreakpoints)
        for pbp in preferredBreakpoints:
            bp_start = utilities.timecodeToFrames(pbp[0])
            bp_end = utilities.timecodeToFrames(pbp[1])
            timecode = utilities.getMidpoint(bp_start, bp_end)
            relative_timecode = utilities.roundPartial(timecode / contentLength, 0.02)
            if relative_timecode >= 1:
                print("Bigger than 1")
                print(prod['ID'])
                print("frames timecode " + str(timecode))
                print("frames contentLength " + str(contentLength))
                print("relative timecode " + str(relative_timecode))
                print("som " + som)
                print("eom " + eom)
                print("bpcodes: " + pbp[0] + "  " + pbp[1])

            appendJsonDict(str(relative_timecode), noBreakpoints)

    # Closing file
    f.close()

def plotBreakpoints(i):
    """
    Get breakpoints from file and plot them on a graph
    (for specified range of content length)
    """
    dict_file = "%s_dict.json" % i
    if os.path.exists(dict_file):
        f = open(dict_file, 'r')
        count_dict = json.load(f)
        count_dict = {float(k): v for k, v in count_dict.items()}
        count_dict = dict(sorted(count_dict.items()))
        # print(count_dict)
        f.close()

        f = open(dict_file, 'w')
        f.truncate()
        json.dump(count_dict, f)
        f.close()

        plt.plot(list(count_dict.keys()), list(count_dict.values()))
        plt.xlabel("Relative time of a breakpoint")
        plt.ylabel("Frequency")
        plt.title(f"Frequency of breakpoints using {i} breakpoints")
        plt.xlim([0, 1])
        plt.show()


## Plot timecode breakpoints
## Use one of these to populate dictionary files:
# getBreakpoints()
# extract_breakpoints()

#Plot the frequencies stored in dictionary json files
for i in range(1, max_breakpoints):
    plotBreakpoints(i)