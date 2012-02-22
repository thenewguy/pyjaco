import os

special_globals = {
    "__name__": None,
    "__builtins__": None,
    "__module__": None
}

def dotted_to_hierarchy(dotted):
    hierarchy = []
    pieces = "%s." % dotted
    while pieces and pieces.count('.'):
        pieces = os.path.splitext(pieces)[0]
        hierarchy.insert(0, pieces)
    return hierarchy