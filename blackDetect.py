import ffmpeg
import tempfile
import re
from utilities import timecodeToFrame


"""
Use ffmpeg to detect black frames
Output this as time series data for analysis
"""


def getStartAndEnd(obj):
    """
    Get start and end of content from API using production number
    In seconds
    """
    start = timecodeToFrame(obj['som'])
    end = timecodeToFrame(obj['eom'])
    essence = timecodeToFrame(obj['soe'])
    startSecond = (start - essence) / 25
    endSecond = (end - essence) / 25
    
    return { 'start': startSecond, 'end': endSecond }


def blackDetect(info):
    """
    Extract loudness data per frame from content
    """
    url = 'current.mp4'
    # trim content using som / eom
    details = getStartAndEnd(info)
    start = int(details['start'])
    end = int(details['end'])
    blackData = [0] * (end - start) * 25

    # Begin ffmpeg process using URL and store in temp file 
    print('Beginning black frame analysis')
    content = ffmpeg.input(url)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        video = (content
            .trim(start=start, end=end) # trim video
            .filter('blackdetect', d=0.04, pic_th=0.98) # black detection - 98% black and min length of 0.04s
            .filter('metadata', mode='print', file=tmp.name) # record start of black frames in tmp
        )
        output = ffmpeg.output(video, 'out.mp4') # , '-'
        out = ffmpeg.overwrite_output(output) # gives permission to overwrite previous 
        out.run(quiet=True) # quiet logs


    with open(tmp.name, 'r') as f:
        blackFrames = []

        for line in f.readlines()[1::2]:
            try:
                num = re.search('=(.+?)\n', line).group(1)
                blackFrames.append(int(float(num) * 25) - (start * 25)) # correcty for trim
            except:
                print('Failed to read')

        for idx, frame in enumerate(blackFrames):
            if idx%2 != 0:
                for i in range(blackFrames[idx-1], frame):
                    if i < len(blackData):
                        blackData[i] = 1

    tmp.close()

    print('Black frame analysis finished')

    return blackData

# object = {
#             'ID': '2_4259_0359.001',
#             "soe": "09:59:30:00",
#             "eoe": "10:20:50:01",
#             "som": "10:00:00:00",
#             "eom": "10:20:40:00",
#             }

# print(len(blackDetect('', object)))
