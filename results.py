import boto3
import requests
import pandas as pd
from utilities import timecodeToFrame


bucket = 'break-data-collection'
s3 = boto3.client('s3')
files = ['10_0137_0015.003']#, '10_1779_0014.001', '2_4263_0245.001', '2_4263_0235.001', '2_4263_0247.001']


def getBreaks(prodId):
    """
    get som and eom
    """
    breaks = []

    try:
        print('Getting part times')
        api = f'https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodId}'
        json = requests.get(api).json()

        if '_embedded' not in json:
            return []

        partTimes = json['_embedded']['programmeVersions'][0]['partTimes']

        if partTimes == None or partTimes == []:
            return []

        som = partTimes[0]['som']  # start of message

        for bp in partTimes:
            type_x = bp['typeDescription']
            bp_som = bp['som']  # start of break
            bp_eom = bp['eom']  # end of break

            if bp_som is None or bp_eom is None:
                return []

            if type_x == "Optional Break Point (Soft Part)" or type_x == "Preferred Break Point (Soft Part)":
                breaks.append([bp_som, bp_eom])

        return [breaks, som]

    except Exception as e:
        'Request failed'
        raise(e)


def main():
    content_list = s3.list_objects_v2(Bucket='break-data-collection', Prefix=f'Predictions/')
    total = 0

    for obj in content_list['Contents']:
        if obj['Key'] == 'Predictions/':
                continue
        
        file = file = obj['Key'].split('/')[1][:-4]
        print('Getting predictions for', file)
        s3_object = s3.get_object(Bucket=bucket, Key=f'Predictions/{file}.csv')
        df = pd.read_csv(s3_object['Body'])

        breakInfo = getBreaks(file[5:])
        breaks = breakInfo[0]
        correct = 0
        som = timecodeToFrame(breakInfo[1])

        print('Calculating score')

        for bp in breaks:
            start = timecodeToFrame(bp[0]) - 10 - som
            end = timecodeToFrame(bp[1]) + 10 - som
            valid = df['Frame'].between(start, end).any()
            
            if valid:
                correct += 1

        rate = 100 * correct / len(breaks)
        total += rate

        print(rate)
    
    total_rate = total / len(content_list['Contents'])
    print('Overall % is', total_rate)

        # groups = [[nums[0]]]          # first group already has first number
                    # for (x, y), d in zip(pairs, diffs):
                    #     if d < 10:
                    #         groups[-1].append(y)  # add to last group
                    #     else:
                    #         groups.append([y])    # start new group


if __name__ == '__main__':
    main()