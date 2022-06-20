import ffmpeg
import boto3

"""
Use ffmpeg to measure audio loudness per frame
Output this as time series data for analysis
"""

s3 = boto3.client('s3')
bucket = 'soft-parted-content-examples'
# key = '1-7133-0001-004.mov'
# url = s3.generate_presigned_url('get_object',
#     Params = { 'Bucket': bucket, 'Key': key },
#     ExpiresIn = 3600,
# )

def extractAudio(key):
    """
    separate audio channels from video
    """
    url = s3.generate_presigned_url('get_object',
        Params = { 'Bucket': bucket, 'Key': key },
        ExpiresIn = 3600,
    )
    stream = ffmpeg.input(url)
    
    return []


def analyseAudio(audio):
    """
    extract loudness data from audio for each frame and add to array
    """

    return []


print(extractAudio('1-7133-0001-004.mov'))