import os

special_globals = {
    "__name__": None,
    "__builtins__": None,
    "__module__": None
}

def create_dotted_path(path, base = None):
    path = os.path.abspath(path)
    if base is None:
        base = os.getcwd()
    base = os.path.abspath(base)
    commonprefix = os.path.commonprefix([path, base])
    path, base, commonprefix = [x.replace('\\','/') for x in (path, base, commonprefix)]
    filename = path[len(commonprefix):].lstrip('/')
    dotted = os.path.splitext(filename)[0].replace('/', '.')
    if dotted.endswith('.__init__'):
        dotted = dotted[:-9]
    return (path, base, filename, dotted)

def dotted_to_hierarchy(dotted):
    hierarchy = []
    pieces = "%s." % dotted
    while pieces and pieces.count('.'):
        pieces = os.path.splitext(pieces)[0]
        hierarchy.insert(0, pieces)
    return hierarchy