# coding: utf-8

"""
Yandex.Maps API wrapper
"""

import xml.dom.minidom
import urllib.parse
import requests

from contextlib import closing
import http.client as httplib

STATIC_MAPS_URL = 'http://static-maps.yandex.ru/1.x/?'
HOSTED_MAPS_URL = 'http://maps.yandex.ru/?'
GEOCODE_URL = 'http://geocode-maps.yandex.ru/1.x/?'

def request(method, url, data=None, headers={}, timeout=None):
    host_port = url.split('/')[2]
    timeout_set = False
    try:
        connection = httplib.HTTPConnection(host_port, timeout = timeout)
        timeout_set = True
    except TypeError:
        connection = httplib.HTTPConnection(host_port)

    with closing(connection):
        if not timeout_set:
            connection.connect()
            connection.sock.settimeout(timeout)
            timeout_set = True

        connection.request(method, url, data, headers)
        response = connection.getresponse()
        return (response.status, response.read())

def _format_point(longitude, latitude):
    return '%0.7f,%0.7f' % (float(longitude), float(latitude),)

def get_map_url(api_key, longitude, latitude, zoom, width, height):
    ''' returns URL of static yandex map '''
    point = _format_point(longitude, latitude)
    params = [
       'll=%s' % point,
       'size=%d,%d' % (width, height,),
       'z=%d' % zoom,
       'l=map',
       'pt=%s' % point,
       'key=%s' % api_key
    ]
    return STATIC_MAPS_URL + '&'.join(params)


def get_external_map_url(longitude, latitude, zoom=14):
    ''' returns URL of hosted yandex map '''
    point = _format_point(longitude, latitude)
    params = dict(
        ll = point,
        pt = point,
        l = 'map',
    )
    if zoom is not None:
        params['z'] = zoom
    return HOSTED_MAPS_URL + urllib.parse.urlencode(params)


def geocode(api_key, address, level, timeout = 2):
    ''' returns (longtitude, latitude,) tuple for given address '''
    try:
        xml = _get_geocode_xml(api_key, address, timeout)
        return _get_coords(xml, level)
    except IOError:
        return None, None

def _get_geocode_xml(api_key, address, timeout = 2):
    url = _get_geocode_url(api_key, address)
    #status_code, response = http.request('GET', url, timeout=timeout)
    res = requests.get(url, timeout = timeout)
    if (res.ok): 
        return res.text
    else:
        print("Request status: [{0}]".format(res.status_code))
        
    return ""

def _get_geocode_url(api_key, address):
    params = urllib.parse.urlencode({'apikey': api_key, 'geocode': address, 'lang':'ru_RU'})
    return GEOCODE_URL + params

def _get_coords(response, level = None):
    rv = None, None
    try:
        dom = xml.dom.minidom.parseString(response)
        geoObjList = dom.getElementsByTagName('GeoObject')
        if (len(geoObjList)):
            posList = geoObjList[0].getElementsByTagName('pos')
            if (len(posList)):
                posData = posList[0].childNodes[0].data
                if (level != None):
                    kindList  = geoObjList[0].getElementsByTagName('kind')
                    if (len(kindList)):
                        for kind in kindList:
                            if (kind.hasChildNodes and 
                                kind.firstChild.nodeType == 3 and
                                kind.firstChild.data == level):

                                rv = tuple(posData.split())
                                break
                else: 
                    rv = tuple(posData.split())
    except IndexError:
        return rv
    return rv
