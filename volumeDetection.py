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

audioData=[]


def getStartAndEnd(prodID):
    """
    Get start and end of content from API using production number
    In seconds
    """
    # Transform id to correct format
    prodNo = convertProdID(prodID)
    # Get programme info
    api = f"https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodNo}"
    json = requests.get(api).json()
    keyInfo = json['_embedded']['programmeVersions'][0]['partTimes'][0]
    start = keyInfo['som'].split(':')
    end = keyInfo['eom'].split(':')
    essence = keyInfo['soe'].split(':')
    # Calculate start and end frame number
    som_split = [int(x) for x in start]
    eom_split = [int(x) for x in end]
    essence_split = [int(x) for x in essence]
    som = np.subtract(som_split, essence_split) 
    eom = np.subtract(eom_split, essence_split) 
    startSecond = (som[0] * 3600) + (som [1] * 60) + som[2] + (som[3] / 25)
    endSecond = (eom[0] * 3600) + (eom [1] * 60) + eom[2] + (eom[3] / 25)
    
    return { 'start': startSecond, 'end': endSecond }


def analyseAudio(url, key):
    """
    Extract loudness data per frame from content
    """
    # url= 'LOWRES_10-2465-0175-001.mp4'

    # trim content using som / eom from API
    details = getStartAndEnd(key)
    start = details['start']
    end = details['end']

    # Begin ffmpeg process using URL and store in temp file 
    print('Beginning audio analysis')
    content = ffmpeg.input(url)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        audio = (content
            .filter('asetnsamples', n=1920) # set correct sampling rate to avoid discrepancies
            .filter('atrim', start=int(start), end=int(end)) # trim audio
            .filter('astats', length=0.04, metadata=1, reset=1) # generate stats
            .filter('ametadata', mode='print', key='lavfi.astats.Overall.RMS_level', file=tmp.name) # record loudness in tmp
        )
        output = ffmpeg.output(audio, 'out.aac')
        out = ffmpeg.overwrite_output(output) # gives permission to overwrite previous audio
        out.run(quiet=True) # quiet logs


    with open(tmp.name, 'r') as f:
        for line in f.readlines()[1::2]:
            try:
                loudness = re.search('=(.+?)\n', line).group(1)
                audioData.append(loudness)
            except:
                print('Failed to read')

    tmp.close()

    print('Audio analysis finished')

    return audioData


# print(analyseAudio('LOWRES_10-2465-0175-001.mp4'))