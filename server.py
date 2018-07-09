import json

import bottle
from bottle import route, run, request, response, hook

from elevation import LatLng, Lookup

def get_elevation(latlng):
    """
    Get the elevation at LatLng using the currently opened interface
    :param latlng:
    :return:
    """
    try:
        elevation = Lookup.lookup(latlng)
    except:
        return {
            'latitude': latlng.lat,
            'longitude': latlng.lng,
            'error': 'No such coordinate (%s, %s)' % (latlng.lat, latlng.lng)
        }

    return {
        'latitude': latlng.lat,
        'longitude': latlng.lng,
        'elevation': int(elevation)
    }


@hook('after_request')
def enable_cors():
    """
    Enable CORS support.
    :return: 
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


def lat_lng_from_location(location_with_comma):
    """
    Parse the latitude and longitude of a location in the format "xx.xxx,yy.yyy" (which we accept as a query string)
    :param location_with_comma: 
    :return: 
    """
    try:
        lat, lng = [float(i) for i in location_with_comma.split(',')]
        return LatLng(lat, lng)
    except:
        raise UserWarning(json.dumps({'error': 'Bad parameter format "%s".' % location_with_comma}))


def query_to_locations():
    """
    Grab a list of locations from the query and turn them into [(lat,lng),(lat,lng),...]
    :return: 
    """
    locations = request.query.locations
    if not locations:
        raise UserWarning(json.dumps({'error': '"Locations" is required.'}))

    return [lat_lng_from_location(l) for l in locations.split('|')]


def body_to_locations():
    """
    Grab a list of locations from the body and turn them into [(lat,lng),(lat,lng),...]
    :return: 
    """
    try:
        locations = request.json.get('locations', None)
    except Exception:
        raise UserWarning(json.dumps({'error': 'Invalid JSON.'}))

    if not locations:
        raise UserWarning(json.dumps({'error': '"Locations" is required in the body.'}))

    latlng = []
    for l in locations:
        try:
            lat = l['latitude']
            lng = l['longitude']
            obj = LatLng(float(lat),float(lng))
            latlng.append(obj)
        except KeyError:
            raise UserWarning(json.dumps({'error': '"%s" is not in a valid format.' % l}))

    return latlng


def do_lookup(get_locations_func):
    """
    Generic method which gets the locations in [(lat,lng),(lat,lng),...] format by calling get_locations_func
    and returns an answer ready to go to the client.
    :return: 
    """
    try:
        locations = get_locations_func()
        return {'results': [get_elevation(latlng) for latlng in locations]}
    except UserWarning as e:
        response.status = 400
        response.content_type = 'application/json'
        return e.args[0]

# Base Endpoint
URL_ENDPOINT = '/api/v1/lookup'

# For CORS
@route(URL_ENDPOINT, method=['OPTIONS'])
def cors_handler():
    return {}

@route(URL_ENDPOINT, method=['GET'])
def get_lookup():
    """
    GET method. Uses query_to_locations.
    :return: 
    """
    return do_lookup(query_to_locations)


@route(URL_ENDPOINT, method=['POST'])
def post_lookup():
    """
        GET method. Uses body_to_locations.
        :return: 
        """
    return do_lookup(body_to_locations)

#run(host='0.0.0.0', port=8080)
run(host='0.0.0.0', port=8080, server='gunicorn', workers=4)
