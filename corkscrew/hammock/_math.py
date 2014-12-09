""" hammock._math

    a bunch of hacks until i figure out how to use geo-mongo.
"""
def all_floats(points):
    _points = []
    for p in points:
        _points.append(map(float, p))
    return _points

def box(points):
    if not points:
        return None, None, None, None
    points = [ [p[1], p[2]] for p in points] # drop label
    points = all_floats(points)
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return min(lats), min(lons), max(lats), max(lons)

def calculate_center(points):
    if not points:
        return None, None
    points = [ [p[1], p[2]] for p in points] # drop label
    points = all_floats(points)
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    lat = max(lats) + min(lats)/2.0
    lon = max(lons) + min(lons)/2.0
    return lat,lon
