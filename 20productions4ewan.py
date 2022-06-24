import numpy as np
import matplotlib.pyplot as plt
import bisect
import requests
import json
from os.path import exists
from os import path
import utilities

"""
Reads an input json file containing production ID's and writes a json file with Production objects containing
optional and preferred breakpoints
"""

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
        print('added ' + type + " " + som + " " + eom)

    def clearBreakpoints(self):
        self.optionalBreakpoints.clear()
        self.preferredBreakpoints.clear()

    def getID(self):
        return self.ID

def getProductionObj(prodNo):
    """
    If there are optional/preferred breakpoints found in a production, return production object
    """
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    valid_breakpoints = False
    production = Production(prodNo)
    production.clearBreakpoints()
    if '_embedded' in json:
        breakpointParts = json['_embedded']['programmeVersions'][0]['partTimes']
        if breakpointParts:
            # get content info; content length and number of breakpoints
            soe = breakpointParts[0]['soe']
            som = breakpointParts[0]['som']
            eom = breakpointParts[0]['eom']
            production.setTimecodes(soe, som, eom)

            startOfMessage = utilities.timecodeToFrames(som)
            endOfMessage = utilities.timecodeToFrames(eom)
            contentLength = endOfMessage - startOfMessage
            noBreakpoints = utilities.getPrefNoBreakpoints(contentLength, 'content')

            print("contentLength " + str(contentLength))
            print("noBreakpoints " + str(noBreakpoints))

            # store each breakpoint in production object
            if contentLength != 0 and noBreakpoints != 0:
                for i in range(1, len(breakpointParts)):
                    part = breakpointParts[i]
                    type_x = part['typeDescription']
                    if type_x == "Optional Break Point (Soft Part)" or type_x == "Preferred Break Point (Soft Part)":
                        production.addBreakpoint(part['som'], part['eom'], type_x)
                        valid_breakpoints = True
            else:
                print("0 content length")
        else:
            print("no parts")
    else:
        print("empty")

    if valid_breakpoints:
        return production

    return None


def getPreferredOptionalBreakpoints(desired_number=20, read_file='ewan_input_prodIDs.json', write_file='ewan_results.json'):
    """
    Read production ID's from read_file and write 20 productionID's to write_file
    Create the write_file prior to calling this function and set it up with:
    {
    "data": []
    }
    """
    # Get prod nos from read_file
    prodNos = []
    f = open(read_file)
    data = json.load(f)
    for entry in data['data']['entries']:
        prodNos.append(utilities.convertProdNo(entry['historicalId']))  # change formatting
    f.close()

    # get breakpoints and write to write_file
    count = 0

    for j in range(0, len(prodNos)):
        if count == desired_number:
            break
        else:
            prodNo = prodNos[j]
            print(prodNo)
            p = getProductionObj(prodNo)

            if p:
                count += 1
                # Check if file exists
                if path.isfile(write_file) is False:
                    raise Exception("File not found")
                print(p.__dict__)
                wf = open(write_file)
                production_arr = json.load(wf)
                production_arr['data'].append(p.__dict__)
                with open(write_file, 'w') as json_file:
                    json.dump(production_arr, json_file, indent=4, separators=(',', ': '))
                print('Successfully appended to the JSON file')
                wf.close()

    if count != desired_number:
        print("didn't find %s valid prod id's" % str(desired_number))


getPreferredOptionalBreakpoints()
