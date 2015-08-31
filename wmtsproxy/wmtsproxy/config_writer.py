import yaml
import sys

from mapproxy.srs import SRS
from mapproxy.util.py import reraise_exception

from . import csv
from .capabilities import parsed_wmts_capabilities, parsed_wms_capabilities
from .grid import make_mapproxy_grid
from .exceptions import ConfigWriterError, FeatureError, TileMatrixError, UserError, ServiceError
from .utils import is_supported_srs


DEFAULT_CACHE_TYPE = 'file'

def mangle_name(name):
    """remove unsafe characters from name"""
    return name.replace(':', '_')

def mapproxy_conf_from_wms_capabilities(mapproxy_conf, cap, service_name, layer_name=None, srs=None, timestamp=None):
    cache_suffix = '_cache'
    if timestamp:
        cache_suffix = '_%d_cache' % timestamp

    def _add_source(mapproxy_conf, layer_name, layer, srs):
        source = {
            'type': 'wms',
            'supported_srs': srs,
            'req': {
                'url': layer['url'],
                'layers': layer['name'],
                'transparent': not layer['opaque']
            }
        }

        if len(srs) == 1 and srs[0] in layer['bbox_srs'].keys():
            source['coverage'] = {
                'bbox': layer['bbox_srs'][srs[0]],
                'srs': srs[0]
            }
        elif layer['llbbox']:
            source['coverage'] = {
                'bbox': layer['llbbox'],
                'srs': 'EPSG:4326'
            }
        elif len(layer['bbox_srs']) > 0:
            bbox_srs_name = layer['bbox_srs'].keys()[0]
            source['coverage'] = {
                'bbox': layer['bbox_srs'][bbox_srs_name],
                'srs': bbox_srs_name
            }

        mapproxy_conf['sources'][mangle_name(layer_name) + '_source'] = source

    def _add_cache(mapproxy_conf, service_name, layer_name):
        mapproxy_conf['caches'][mangle_name(service_name) + cache_suffix] = {
            'sources': [mangle_name(layer_name) + '_source'],
            'grids': ['webmercator'],
            'cache': {
                'type': DEFAULT_CACHE_TYPE,
            },
        }

    def _add_layer(mapproxy_conf, service_name, layer):
        mapproxy_conf['layers'].append({
            'name': 'map',
            'title': layer['title'],
            'sources': [mangle_name(service_name) + cache_suffix],
        })

    if layer_name is None:
        raise ConfigWriterError('No layer given')

    layer = None

    for cap_layer in cap.layers_list():
        if layer_name == cap_layer['name']:
            layer = cap_layer
            break

    if layer is None:
        raise ConfigWriterError('Layer "%s" not found' % layer_name)

    if srs and srs not in layer['srs']:
        raise ConfigWriterError('Given srs "%s" doesn\'t exists for layer "%s"' % (srs, layer_name,))

    srs = [srs] if srs is not None else list(layer['srs'])

    for _srs in srs:
        if not is_supported_srs(_srs):
            raise FeatureError('Unsupported SRS "%s"' % _srs)

    _add_source(mapproxy_conf, layer_name, layer, srs)
    _add_cache(mapproxy_conf, service_name, layer_name)
    _add_layer(mapproxy_conf, service_name, layer)

    return mapproxy_conf


def mapproxy_conf_from_wmts_capabilities(mapproxy_conf, cap, service_name, layer_name=None, matrix_set_id=None, dimensions=None, timestamp=None):
    cache_suffix = '_cache'
    tmpcache_suffix = '_tmpcache'
    if timestamp:
        cache_suffix = '_%d_cache' % timestamp
        tmpcache_suffix = '_%d_tmpcache' % timestamp

    def _add_grid(mapproxy_conf, grid):
        if grid['name'] in ['GLOBAL_GEODETIC', 'GLOBAL_MERCATOR', 'GLOBAL_WEBMERCATOR']:
            grid['name'] += '_'
        if grid['name'] not in mapproxy_conf['grids'].keys():
            mapproxy_conf['grids'][grid['name']] = {
                'srs': grid['srs'].srs_code,
                'res': grid['resolutions'],
                'tile_size': list(grid['tile_size']),
                'bbox': list(grid['bbox']),
                'origin': 'nw'
            }

    def _add_layer(mapproxy_conf, service_name, layer):
        mapproxy_conf['layers'].append({
            'name': 'map',
            'title': layer['title'],
            'sources': [mangle_name(service_name) + cache_suffix]
        })

    def _add_cache(mapproxy_conf, service_name, layer_name, grid_name):
        mapproxy_conf['caches'][mangle_name(service_name) + tmpcache_suffix] = {
            'grids': [grid_name],
            'sources': [mangle_name(layer_name) + '_source'],
            'cache': {
                'type': DEFAULT_CACHE_TYPE,
            },
        }

        mapproxy_conf['caches'][mangle_name(service_name) + cache_suffix] = {
            'grids': ['webmercator'],
            'sources': [mangle_name(service_name) + tmpcache_suffix],
            'meta_size': [6, 6],
            'meta_buffer': 0,
            'concurrent_tile_creators': 4,
            'cache': {
                'type': DEFAULT_CACHE_TYPE,
            },
        }

    def _add_source(mapproxy_conf, layer_name, layer, tile_matrix_set, grid):
        source_url = None

        url_parameter = {
            'tile_matrix_set': tile_matrix_set['id'],
            'layer': layer_name,
            'format': layer['formats'][0],
             # WMTS does not provide opacity information, depend on format
            'transparent': True if layer['formats'][0] == 'image/png' else False,
        }

        if 'dimensions' in layer:
            for dim in layer['dimensions']:
                # replace dimension variables with user provided values...
                if dim['id'] in dimensions:
                    url_parameter[dim['id']] = dimensions[dim['id']]
                # or with default values
                else:
                    default_value = dim['default'] if 'default' in dim else ''
                    url_parameter[dim['id']] = default_value
        source_url = layer['url_template'] % url_parameter
        if grid['prefix'] is not None:
            source_url = source_url.replace('%(z)s', '%s%%(z)s' % grid['prefix'])

        grid_4326_bbox = grid['srs'].transform_bbox_to(SRS(4326), grid['bbox'])

        coverage_bbox = [
            max(grid_4326_bbox[0], layer['bbox'][0]),
            max(grid_4326_bbox[1], layer['bbox'][1]),
            min(grid_4326_bbox[2], layer['bbox'][2]),
            min(grid_4326_bbox[3], layer['bbox'][3])
        ]

        mapproxy_conf['sources'][mangle_name(layer_name) + '_source'] = {
            'type': 'tile',
            'url': source_url,
            'grid': grid['name'],
            'coverage': {
                'bbox': coverage_bbox,
                'srs': 'EPSG:4326'
            },
            'on_error': {
                204: {
                    'response': 'transparent',
                    'cache': False
                },
                400: {
                    'response': 'transparent',
                    'cache': False
                }
            }
        }

    if layer_name is None:
        raise ConfigWriterError('No layer given')
    if layer_name not in cap.layers.keys():
        raise ConfigWriterError('Layer "%s" not found' % layer_name)

    cap_layer = cap.layers[layer_name]

    if not 'url_template' in cap_layer:
        raise ConfigWriterError('Layer "%s" have no requestable url' % layer_name)

    if len(cap_layer['matrix_sets']) == 0:
        raise ConfigWriterError('Layer "%s" have no matrix set' % layer_name)

    matrix_set = None
    for cap_matrix_set in cap_layer['matrix_sets']:
        if matrix_set_id and matrix_set_id == cap_matrix_set['id']:
            matrix_set = cap_matrix_set
            break

    if matrix_set_id and matrix_set is None:
        raise ConfigWriterError('Given matrix set %s doesn\'t exists for layer "%s"' % (matrix_set_id, layer_name,))

    if matrix_set is None:
        matrix_set = cap_layer['matrix_sets'][0]

    try:
        mapproxy_grid = make_mapproxy_grid(cap_matrix_set)
    except TileMatrixError as ex:
        reraise_exception(FeatureError('Tile matrix "%s" not supported' % cap_matrix_set['id'], ex.args[0]), sys.exc_info())

    _add_grid(mapproxy_conf, mapproxy_grid)
    _add_layer(mapproxy_conf, service_name, cap_layer)
    _add_source(mapproxy_conf, layer_name, cap_layer, cap_matrix_set, mapproxy_grid)
    _add_cache(mapproxy_conf, service_name, layer_name, mapproxy_grid['name'])

    return mapproxy_conf


def write_mapproxy_conf(mapproxy_conf, filename):
    content = yaml.safe_dump(mapproxy_conf, default_flow_style=False)
    with open(filename, 'wb') as f:
        f.write(content)

def mapproxy_config_from_csv(id, base_file, csv_config_file=None):
    try:
        rec = csv.from_csv(id, csv_config_file)
    except ServiceError as ex:
        raise ex
    except Exception as ex:
        reraise_exception(ServiceError('Unable to load configuration', ex.args[0]), sys.exc_info())

    mapproxy_conf = {
        'base': [base_file],
        'services': {
            'wmts': {}
        },
        'layers': [],
        'caches': {},
        'sources': {},
        'grids': {
            'webmercator': { # custom grid for different name in WMTS URLs
                'base': 'GLOBAL_WEBMERCATOR',
            }
        },
        'globals': {},
    }

    if rec.type == 'wms':
        cap = parsed_wms_capabilities(rec.url)
        return mapproxy_conf_from_wms_capabilities(mapproxy_conf, cap, rec.id, rec.layer_name, rec.system_id,
            timestamp=rec.timestamp)
    elif rec.type == 'wmts':
        cap = parsed_wmts_capabilities(rec.url)
        return mapproxy_conf_from_wmts_capabilities(mapproxy_conf, cap, rec.id, rec.layer_name, rec.system_id, rec.dimensions,
            timestamp=rec.timestamp)
    else:
        raise UserError('No valid capabilities type given')

