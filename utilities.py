def convertProdID(id):
    """
    Assumes x_x_x.x format
    """
    # check = id.split('_')[1] if '_' in id else id
    split = id.split('_')
    partJoined = '/'.join(split)
    new = partJoined.replace('.', '#')

    return new


def timecodeToFrame(time):
    """
    Converts timecode to frame count
    """
    split = time.split(":")
    ints = [int(x) for x in split]
    frameCount = (ints[0] * 3600 * 25) + (ints [1] * 60 * 25) + (ints[2] * 25) + ints[3]

    return frameCount


def calculateLength(obj):
    """
    Calculate the length of content in frames from som and eom
    """
    start = timecodeToFrame(obj['som'])
    end = timecodeToFrame(obj['eom'])

    return end - start