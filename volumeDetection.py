from tracemalloc import start
import ffmpeg
import boto3
import tempfile
import re
import requests
import numpy as np
from utilities import convertProdID

"""
Use ffmpeg to measure audio loudness per frame
Output this as time series data for analysis
"""

s3 = boto3.client('s3')
bucket = 'soft-parted-examples'
audioData=[]


def getStartAndEnd(prodID):
    """
    Get start and end of content from API using production number
    In seconds
    """
    print('Fetching content time data')

    prodNo = convertProdID(prodID.split('.')[0])
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    keyInfo = json['_embedded']['programmeVersions'][0]['partTimes'][0]
    start = keyInfo['som'].split(':')
    end = keyInfo['eom'].split(':')
    essence = keyInfo['soe'].split(':')
    # start='10:00:00:00'.split(':')
    # end='11:25:40:21'.split(':')
    som_split = [int(x) for x in start]
    eom_split = [int(x) for x in end]
    essence_split = [int(x) for x in essence]
    som = np.subtract(som_split, essence_split) 
    eom = np.subtract(eom_split, essence_split) 
    startSecond = (som[0] * 3600) + (som [1] * 60) + som[2] + (som[3] / 25)
    endSecond = (eom[0] * 3600) + (eom [1] * 60) + eom[2] + (eom[3] / 25)
    
    return { 'start': startSecond, 'end': endSecond }


def extractAudio(key):
    """
    separate audio channels from video
    """
    url = s3.generate_presigned_url('get_object',
        Params = { 'Bucket': bucket, 'Key': key },
        ExpiresIn = 3600,
    )
    # url= 'LOWRES_2-4259-0359-001.mp4'
    # trim content using som / eom from API
    content = ffmpeg.input(url)
    start = getStartAndEnd(key)['start']
    end = getStartAndEnd(key)['end']

    print('Beginning audio analysis')

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        audio = (content
            .filter('atrim', start=int(start), end=int(end))
            .filter('astats', length=0.04, metadata=1, reset=1)
            .filter('ametadata', mode='print', key='lavfi.astats.Overall.RMS_level', file=tmp.name)
        )
        output = ffmpeg.output(audio, 'out.aac')
        out = ffmpeg.overwrite_output(output)
        out.run(quiet=True)


    with open(tmp.name, 'r') as f:
        for line in f.readlines()[1::2]:
            try:
                loudness = re.search('=(.+?)\n', line).group(1)
                audioData.append(loudness)
            except:
                print('Failed to read')

    tmp.close()

    print('end ffmpeg')

    return audioData


print(extractAudio('1-7133-0001-004.mov'))