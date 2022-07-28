import urllib.parse, urllib.request
import shutil
from volumeDetection import analyseAudio
from evenDistributionScore import breakPattern
from blackDetect import blackDetect
from utilities import convertProdID, timecodeToFrame, calculateLength
import pandas as pd
import numpy as np
import requests
import boto3
from io import StringIO
import json


f = open('productions.json')
input_data = json.load(f)['data']
session = boto3.Session(profile_name='default')
session_content = boto3.Session(profile_name='content')


def getLocation(prodId):
    """
    Use id to get bucket location from API
    """
    parsed = urllib.parse.quote(convertProdID(prodId))
    fully_parsed = parsed.replace('/', '%2F')
    try:
        print('Getting content location of ', prodId)
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
    s3 = session_content.client('s3')

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
    start = timecodeToFrame(obj['som'])
    adjusted = [item - start for item in ordered]
    length = calculateLength(obj)
    breaks = [0] * length
    
    for idx, point in enumerate(adjusted):
        if idx%2 != 0:
            for i in range(adjusted[idx-1], point+1):
                breaks[i] = 1

    return breaks


def checkCompletion(ID):
    """
    check whether id already analysed
    """
    s3 = session.client('s3')
    response = s3.list_objects_v2(Bucket='break-data-collection', Prefix=ID, MaxKeys=1)

    if 'Contents' in response:
        for obj in response['Contents']:
            if ID == obj['Key']:
                return True
            
        return False
    else:
        return False


def main():

    try:
        for obj in input_data:
            key = obj['ID']
            if key[-3:] == '002':
                continue
            filename = key.replace('/', '_')
            full_name = f'{filename}.csv'
            length = calculateLength(obj)
            print('Analysing id: ', key) 
            location = getLocation(key)
            if location:
                url = getUrl(location)

                if checkCompletion(full_name):
                    print('ID already analysed, skipping.')
                    continue

                with urllib.request.urlopen(url) as response, open('current.mp4', 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)

                breaks = formatBreaks(obj)
                audio = analyseAudio(obj)
                blackFrames = blackDetect(obj)
                distibutionScores = breakPattern(length)
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
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                s3_upload = session.resource('s3')
                s3_upload.Object('break-data-collection', f'New/{full_name}').put(Body=csv_buffer.getvalue())
                print(key, 'metadata uploaded to bucket')
            except:
                print('Failed to upload to s3 bucket')

    except KeyboardInterrupt:
        print('Interupted.')


if __name__ == '__main__':
    main()
    # getUrl(getLocation('10_0137_0015.003'))