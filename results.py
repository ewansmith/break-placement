import boto3
import requests
import pandas as pd


bucket = 'break-data-collection'
s3 = boto3.client('s3')
files = ['10_0137_0015.003', '10_1779_0014.001', '2_4263_0245.001', '2_4263_0235.001', '2_4263_0247.001']


def getBreaks(prodId):
    """
    get som and eom
    """
    breaks = []

    try:
        print('Getting content details of ', prodId)
        api = f'https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodId}'
        json = requests.get(api).json()

        if '_embedded' not in json:
            return []

        partTimes = json['_embedded']['programmeVersions'][0]['partTimes']

        if partTimes == None or partTimes == []:
            return []

        for bp in partTimes:
            type_x = bp['typeDescription']
            bp_som = bp['som']  # start of break
            bp_eom = bp['eom']  # end of break

            if bp_som is None or bp_eom is None:
                return []

            if type_x == "Optional Break Point (Soft Part)" \
                or type_x == "Preferred Break Point (Soft Part)":
                breaks.append([bp_som. bp_eom])

        return breaks

    except Exception as e:
        'Request failed'
        raise(e)


def main():

    for file in files:
        s3_object = s3.get_object(Bucket=bucket, Key=f'PRED-{file}.csv')
        df = pd.read_csv(s3_object['Body'])

        breaks = getBreaks(file)



        # groups = [[nums[0]]]          # first group already has first number
                    # for (x, y), d in zip(pairs, diffs):
                    #     if d < 10:
                    #         groups[-1].append(y)  # add to last group
                    #     else:
                    #         groups.append([y])    # start new group