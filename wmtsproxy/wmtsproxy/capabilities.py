from __future__ import absolute_import

import requests
import sys

from cStringIO import StringIO

from mapproxy.util.py import reraise_exception
from mapproxy.util.ext.wmsparse.parse import parse_capabilities as parse_wms_capabilities
from mapproxy.grid import tile_grid

from . import csv
from .wmtsparse import parse_capabilities as parse_wmts_capabilities, WMTSCapabilities
from .exceptions import CapabilitiesError, UserError, FeatureError, ServiceError
from .utils import is_supported_srs


webmercator_grid = tile_grid(3857, origin='nw')

def parsed_capabilities(cap_url):
    cap_doc = request_capabilities(cap_url)
    try:
        cap = parse_wmts_capabilities(cap_doc)
    except Exception as ex:
        try:
            cap_doc.seek(0)
            cap = parse_wms_capabilities(cap_doc)
        except Exception as ex:
            reraise_exception(CapabilitiesError('not a valid capabilities document', ex.args[0]), sys.exc_info())
    return cap

def parsed_wmts_capabilities(cap_url):
    cap_doc = request_capabilities(cap_url)
    try:
        cap = parse_wmts_capabilities(cap_doc)
    except Exception as ex:
        reraise_exception(CapabilitiesError('not a valid capabilities document', ex.args[0]), sys.exc_info())
    return cap

def parsed_wms_capabilities(cap_url):
    cap_doc = request_capabilities(cap_url)
    try:
        cap = parse_wms_capabilities(cap_doc)
    except Exception as ex:
        reraise_exception(CapabilitiesError('not a valid capabilities document', ex.args[0]), sys.exc_info())
    return cap


def request_capabilities(cap_url):
    try:
        response = requests.get(cap_url)
    except requests.exceptions.RequestException as ex:
        reraise_exception(CapabilitiesError('Opening given capabilities url failed.', ex.args[0]), sys.exc_info())
    if not response.ok:
        raise CapabilitiesError('Opening given capabilities url failed.', 'response.ok False')

    return StringIO(response.content)

def cap_dict(cap_url):
    cap = parsed_capabilities(cap_url)
    if isinstance(cap, WMTSCapabilities):
        return wmts_cap_dict(cap)
    return wms_cap_dict(cap)

def wmts_cap_dict(cap):
    cap_layers = cap.layers.items()

    layers = []
    for layer_name, layer in cap_layers:
        layers.append({
            'name': layer_name,
            'title': layer['title'],
            'matrix_sets': [matrix_set['id'] for matrix_set in layer['matrix_sets']],
            'llbbox': layer['bbox'],
        })
        dimension = wmts_layer_dimensions(layer)
        if dimension:
            layers[-1]['dimensions'] = dimension
    return {
        'type': 'wmts',
        'title': cap.service['title'],
        'layers': layers,
    }

def wmts_layer_dimensions(layer):
    dimensions = {}
    for dim in layer['dimensions']:
        dimensions[dim['id']] = {
            'value': dim['value'],
            'default': dim['default'],
        }
    return dimensions


def sorted_srs_list(srs):
    """
    "sort" list of SRS. Moves EPSG:3857, EPSG:900913 and EPSG:4326 to the
    front, keeps order of other projections.
    """
    result = list(srs)
    if 'EPSG:4326' in result:
        result.pop(result.index('EPSG:4326'))
        result.insert(0, 'EPSG:4326')
    if 'EPSG:900913' in result:
        result.pop(result.index('EPSG:900913'))
        result.insert(0, 'EPSG:900913')
    if 'EPSG:3857' in result:
        result.pop(result.index('EPSG:3857'))
        result.insert(0, 'EPSG:3857')
    return result

def wms_cap_dict(cap):
    try:
        cap_layers = cap.layers_list()
    except Exception as ex:
        reraise_exception(CapabilitiesError('not a valid capabilities document', ex.args[0]), sys.exc_info())

    layers = []
    for layer in cap_layers:
        srs = []
        for _srs in sorted_srs_list(layer['srs']):
            # don't add unsupported srs
            if not is_supported_srs(_srs):
                continue
            srs.append(_srs)
        layers.append({
            'name': layer['name'],
            'title': layer['title'],
            'srs': srs,
            'llbbox': layer['llbbox'],
        })
        if layer['res_hint']:
            min_res, max_res = layer['res_hint']
            if min_res is not None:
                layers[-1]['min_level'] = webmercator_grid.closest_level(min_res)
            if max_res is not None:
                layers[-1]['max_level'] = webmercator_grid.closest_level(max_res)

    return {
        'type': 'wms',
        'title': cap.metadata()['title'],
        'layers': layers,
    }

def res_to_zoom(res):
    webmercator_grid.closest_level(res)
    print res


def add_wmts_layer(cap_url, layer_name, matrix_set, csv_config_file, dimensions=None):
    cap = parsed_wmts_capabilities(cap_url)

    if not layer_name in cap.layers.keys():
        raise UserError('Layer "%s" not found in given capabilities document' % layer_name)
    found = False
    for ms in cap.layers[layer_name]['matrix_sets']:
        if ms['id'] == matrix_set:
            found = True
            break

    if not found:
        raise UserError('MatrixSet "%s" not supported by layer "%s"' % (matrix_set, layer_name,))

    try:
        mapproxy_id = csv.to_csv(csv_config_file, 'wmts', cap_url, layer_name, matrix_set, dimensions=dimensions)
    except Exception as ex:
        reraise_exception(ServiceError('Creating layer failed', ex.args[0]), sys.exc_info())

    return mapproxy_id

def add_wms_layer(cap_url, layer_name, srs, csv_config_file):
    cap = parsed_wms_capabilities(cap_url)

    layer = None
    for cap_layer in cap.layers_list():
        if cap_layer['name'] == layer_name:
            layer = cap_layer
            break
    if layer is None:
        raise UserError('Layer "%s" not found in given capabilities document' % layer_name)
    if srs not in layer['srs']:
        raise UserError('SRS "%s" not supported by layer "%s"' % (srs, layer_name,))
    if not is_supported_srs(srs):
        raise FeatureError('Unsupported SRS "%s"' % srs)

    try:
        mapproxy_id = csv.to_csv(csv_config_file, 'wms', cap_url, layer_name, srs)
    except Exception as ex:
        reraise_exception(ServiceError('Creating layer failed', ex.args[0]), sys.exc_info())

    return mapproxy_id


