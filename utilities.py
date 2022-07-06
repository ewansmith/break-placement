def convertProdID(id):
    """
    Assumes x_x_x.x format
    """
    # check = id.split('_')[1] if '_' in id else id
    split = id.split('_')
    partJoined = '/'.join(split)
    new = partJoined.replace('.', '#')

    return new

def roundPartial(x, base=0.02):
    '''
    Return x rounded to 5
    '''
    return base * round(x / base)

def getMidpoint(start, end):
    '''
    Return the integer exactly halfway between start and end
    '''
    return (start + end) / 2

def timecodeToFrames(timecode):
    '''
    Return timecode in number of frames
    '''
    temp = timecode.split(':')
    answer = [int(x) for x in temp]

    hours = (answer[0]-10) * (3600 * 25)
    mins = answer[1] * 60 * 25
    secs = (answer[2] * 25)
    return hours + mins + secs + answer[3]

def count_elements(seq):
    """
    Tally elements from `seq' and return dictionary
    """
    dict = {}
    for i in seq:
        dict[i] = dict.get(i, 0) + 1
    return dict

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
