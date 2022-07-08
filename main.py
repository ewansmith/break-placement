import urllib.parse
from volumeDetection import analyseAudio
from evenDistributionScore import breakPattern
from RekognitionTest import getRekResults
from blackDetect import blackDetect
from utilities import convertProdID, timecodeToFrame, calculateLength
import pandas as pd
import numpy as np
import requests
import boto3
from io import StringIO
import json


f = open('more_input.json')
input_data = json.load(f)['data']
session = boto3.Session(profile_name='content')
s3 = session.client('s3')


def getLocation(prodId):
    """
    Use id to get bucket location from API
    """
    parsed = urllib.parse.quote(convertProdID(prodId))
    fully_parsed = parsed.replace('/', '%2F')
    try:
        print('Getting content location')
        api = f'https://access-services-api.prd.am.itv.com/browse/production-number/{fully_parsed}'
        json = requests.get(api).json()
        info = json['assets'][0]
        bucket = info['s3Location']['bucketName']
        key = info['s3Location']['key']
        prod = info['productionNumber']

        return { 
            'bucket': bucket,
            'key': key,
            'prod': prod,
        }

    except:
        return None


def getUrl(info):
    """
    Generate URL from bucket location of ID
    """
    url = s3.generate_presigned_url('get_object',
        Params = { 'Bucket': info['bucket'], 'Key': info['key'] },
        ExpiresIn = 3600,
    )

    print('Content at: ', url)

    return url
     

def formatBreaks(obj):
    """
    Format breaks to use as training data
    """
    breakpoints = obj['preferredBreakpoints']
    optionalBreakpoints = obj['optionalBreakpoints']
    breakpoints.extend(optionalBreakpoints)
    converted = [timecodeToFrame(item) for arr in breakpoints for item in arr]
    ordered = sorted(converted)
    start = timecodeToFrame(obj['soe'])
    adjusted = [item - start for item in ordered]
    length = calculateLength(obj)
    breaks = [0] * length
    
    for idx, point in enumerate(adjusted):
        if idx%2 != 0:
            for i in range(adjusted[idx-1], point+1):
                breaks[i] = 1

    return breaks

# object = {
#     'ID': '2_4259_0359.001',
#     "soe": "09:59:30:00",
#     "eoe": "10:20:50:01",
#     "som": "10:00:00:00",
#     "eom": "10:20:40:00",
#      "optionalBreakpoints": [
#                 [
#                     "10:19:45:08",
#                     "10:19:45:12"
#                 ],
#             ],
#             "preferredBreakpoints": [
#                 [
#                     "10:14:30:02",
#                     "10:14:30:03"
#                 ],
#             ],
# }


def main():

    try:
        for obj in input_data:
            # obj = object
            key = obj['ID']
            if key[-3:] == '002':
                continue
            length = calculateLength(obj)
            print('Analysing id: ', key) 
            location = getLocation(key)
            if location:
                url = getUrl(location)
                breaks = formatBreaks(obj)
                audio = analyseAudio(url, obj)
                blackFrames = blackDetect(url, obj)
                distibutionScores = breakPattern(length)
                # shots = getRekResults('itv-cdt-prd-lowres', key)
            else: 
                print('ERROR: no location found for id: ', key)
                continue


            # Ensure audio is same length - sometimes crops a few frames off
            audio.extend(np.zeros(length - len(audio)))
            blackFrames.extend(np.zeros(length - len(blackFrames)))

            try:
                # Collect data in a dataframe
                data = { 'breaks': breaks, 'audio': audio, 'blackFrames': blackFrames, 'distribution': distibutionScores }
                df = pd.DataFrame(data, columns=['breaks', 'audio', 'blackFrames', 'distribution'])
            except:
                print('ERROR: length mismatch in data for id ', key)
                continue
            
            try:
                # Convert dataFrame to csv and upload
                upload_session = boto3.Session(profile_name='default')
                s3_upload = upload_session.resource('s3')
                bucket = s3_upload.Bucket('break-data-collection')
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                filename = key.replace('/', '_')
                s3_upload.Object('break-data-collection', f'{filename}.csv').put(Body=csv_buffer.getvalue())
                print(key, 'metadata uploaded to bucket')
                break
            except:
                print('Failed to upload to s3 bucket')

    except KeyboardInterrupt:
        print('Interupted.')


if __name__ == '__main__':
    main()