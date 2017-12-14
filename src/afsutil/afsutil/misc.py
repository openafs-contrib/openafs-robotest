
"""Misc functions"""

def flatten(x):
    """Flatten a small list of lists.

    Example:
        flatten( [[1, 2], [3]] ) => [1, 2, 3]
    """
    if not isinstance(x, (list, tuple)):
        return x # skip non-interables, including None
    y = []
    for e in x:
        if isinstance(e, (list, tuple)):
            y.extend(flatten(e))
        else:
            y.append(e)
    return y

def lists2dict(options):
    """ Helper to convert a list of lists of name=value strings to a dict."""
    if isinstance(options, dict):
        return options
    if options is None:
        options = []
    if not isinstance(options, (list, tuple)):
        options = [options]
    options = flatten(options)
    names = {}
    for o in options:
        name,value = o.split('=', 1)
        names[name.strip()] = value.strip()
    return names

def trim(s, x):
    """Trim trailing x from s."""
    if s.endswith(x):
        s = s.rsplit(x,1)[0]
    return s

def uniq(x):
    """Remove dupes from a small list, preserving order."""
    y = []
    for item in x:
        if not item in y:
            y.append(item)
    return y

def flipbase64_encode(n):
    """Encode an integer to a flip-base64, a base64 variant for AFS namei."""
    index = '+=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    base64 = [index[n & 0x3f]]
    n >>= 6
    while n:
        base64.append(index[n & 0x3f])
        n >>= 6
    return ''.join(base64)
