import urllib.parse
from volumeDetection import analyseAudio
from evenDistributionScore import breakPattern
import pandas as pd
import requests
import boto3
from io import StringIO

id_list = {
    '2/4259/0359#001': {
        'som': '',
        'breaks': [0]
    }
}

session = boto3.Session(profile_name='content')
s3 = session.client('s3')

def getLocation(prodId):
    """
    Use id to get bucket location from API
    """
    parsed = urllib.parse.quote(prodId)
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
    url = s3.generate_presigned_url('get_object',
        Params = { 'Bucket': info['bucket'], 'Key': info['key'] },
        ExpiresIn = 3600,
    )

    print('Content at: ', url)

    return url


def main():

    for key in id_list:
        print('Analysing id: ', key) 
        location = getLocation(key)
        if location:
            url = getUrl(location)
            audio = analyseAudio(url, key)
            breaks = [0] * len(audio)
            distibutionScores = breakPattern(len(audio)) # CHECK THIS
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