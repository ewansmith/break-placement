def convertProdID(id):
    """
    Assumes x/x/x#x format
    (not for use with x-x-x?x)
    """
    # check = id.split('_')[1] if '_' in id else id
    split = id.split('/')
    partJoined = '_'.join(split)
    new = partJoined.replace('#', '.')

    return new