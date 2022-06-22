def convertProdID(id):
    """
    Assumes x-x-x-x format
    (not for use with x-x-x#x)
    """
    split = id.split('-')
    partJoined = '_'.join(split[0:3])
    new = '.'.join([partJoined, split[-1]])

    return new