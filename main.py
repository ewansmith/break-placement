import urllib.parse
from volumeDetection import analyseAudio
from evenDistributionScore import breakPattern
from utilities import convertProdID, timecodeToFrame
import pandas as pd
import requests
import boto3
from io import StringIO
import json


f = open('input.json')
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


def calculateLength(obj):
    """
    Calculate the length of content in frames
    """
    start = timecodeToFrame(obj['som'])
    end = timecodeToFrame(obj['eom'])

    return end - start
     

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

    return breaks.count(1)


def main():

    for obj in input_data:
        key = obj['ID']
        length = calculateLength(obj)
        print('Analysing id: ', key) 
        location = getLocation(key)
        if location:
            url = getUrl(location)
            audio = analyseAudio(url, obj)
            breaks = formatBreaks(obj)
            distibutionScores = breakPattern(length)
        else: 
            print('ERROR: no location found for id: ', key)
            continue

        # Collect data in a dataframe
        data = { 'breaks': breaks, 'audio': audio, 'distribution': distibutionScores }
        df = pd.DataFrame(data, columns=['breaks', 'audio', 'distribution'])
        
        try:
            # Convert dataFrame to csv and upload
            upload_session = boto3.Session(profile_name='default')
            s3_upload = upload_session.resource('s3')
            bucket = s3_upload.Bucket('break-data-collection')
            csv_buffer = StringIO()
            df.to_csv(csv_buffer)
            filename = key.replace('/', '_')
            s3_upload.Object('break-data-collection', f'{filename}.csv').put(Body=csv_buffer.getvalue())
            print(key, 'metadata uploaded to bucket')
        except:
            print('Failed to upload to s3 bucket')



if __name__ == '__main__':
    main()