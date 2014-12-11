import re

from mapproxy.srs import SRS

from .exceptions import TileMatrixError

test_grid = {
    'id': 'GoogleCRS84Quad',
    'crs': 'urn:ogc:def:crs:EPSG::4326',
    'tile_matrices': [
        {'id': 'GoogleCRS84Quad:1', 'scale_denom': 2.795411320143589E8, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (2,1)},
        {'id': 'GoogleCRS84Quad:2', 'scale_denom': 1.397705660071794E8, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (4,2)},
        {'id': 'GoogleCRS84Quad:3', 'scale_denom': 6.988528300358972E7, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (8,4)},
        {'id': 'GoogleCRS84Quad:4', 'scale_denom': 3.494264150179486E7, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (16,8)},
        {'id': 'GoogleCRS84Quad:5', 'scale_denom': 1.747132075089743E7, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (32,16)},
        {'id': 'GoogleCRS84Quad:6', 'scale_denom': 8735660.375448715, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (64,32)},
        {'id': 'GoogleCRS84Quad:7', 'scale_denom': 4367830.187724357, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (128,64)},
        {'id': 'GoogleCRS84Quad:8', 'scale_denom': 2183915.093862179, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (256,128)},
        {'id': 'GoogleCRS84Quad:9', 'scale_denom': 1091957.546931089, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (512,256)},
        {'id': 'GoogleCRS84Quad:10', 'scale_denom': 545978.7734655447, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (1024,512)},
        {'id': 'GoogleCRS84Quad:11', 'scale_denom': 272989.3867327723, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (2048,1024)},
        {'id': 'GoogleCRS84Quad:12', 'scale_denom': 136494.6933663862, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (4096,2048)},
        {'id': 'GoogleCRS84Quad:13', 'scale_denom': 68247.34668319309, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (8192,4096)},
        {'id': 'GoogleCRS84Quad:14', 'scale_denom': 34123.67334159654, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (16384,8192)},
        {'id': 'GoogleCRS84Quad:15', 'scale_denom': 17061.83667079827, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (32768,16384)},
        {'id': 'GoogleCRS84Quad:16', 'scale_denom': 8530.918335399136, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (65536,32768)},
        {'id': 'GoogleCRS84Quad:17', 'scale_denom': 4265.459167699568, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (131072,65536)},
        {'id': 'GoogleCRS84Quad:18', 'scale_denom': 2132.729583849784, 'top_left': (90.0, -180.0), 'tile_size': (256, 256), 'grid_size': (262144,131072)},
    ]
}

def merge_bbox(a, b):
    if a is None:
        return b
    if b is None:
        return a

    return (
        min(a[0], b[0]),
        min(a[1], b[1]),
        max(a[2], b[2]),
        max(a[3], b[3]),
    )


crs_urn_re = re.compile('urn:ogc:def:crs:EPSG:(\d*.?\d*):(\d+)')

def crs_to_mapproxy_srs(crs):
    if crs.startswith('EPSG:'):
        return SRS(crs)
    if crs == 'urn:ogc:def:crs:OGC:1.3:CRS84':
        return SRS(4326)

    match = crs_urn_re.match(crs)
    if match:
        return SRS(int(match.group(2)))

split_prefix_re = re.compile('(\d+$)')

def _split_tm_identifier(s):
    """
    >>> _split_tm_identifier('3')
    (3, None)
    >>> _split_tm_identifier('foo')
    (False, None)
    >>> _split_tm_identifier('foo3')
    (3, 'foo')
    >>> _split_tm_identifier('EPSG:4326:9')
    (9, 'EPSG:4326:')
    """
    result = split_prefix_re.search(s)
    if not result:
        return False, None
    start = result.start()
    if start == 0:
        return int(s), None
    return int(s[start:]), s[:result.start()]

def make_mapproxy_grid(tile_matrix_set):
    srs = crs_to_mapproxy_srs(tile_matrix_set['crs'])
    previous_tl = None
    previous_tile_size = None
    resolutions = []
    number = -1
    prefix = None
    for tm in tile_matrix_set['tile_matrices']:
        _number, _prefix = _split_tm_identifier(tm['id'])
        # this works cause
        # In [1]: 2 + False
        # Out[1]: 2
        if not (number + 1) == _number:
            raise TileMatrixError('TileMatrixSet without numeric range identifier')
        number = _number

        if prefix is not None and _prefix != prefix:
            raise TileMatrixError('TileMatrixSet without clearly identifier')
        prefix = _prefix

        tile_size = tm['tile_size']
        if previous_tile_size and tile_size != previous_tile_size:
            raise TileMatrixError('TileMatrixSet with non-uniform TileWidth/TileHeight')
        previous_tile_size = tile_size

        num_tiles = tm['grid_size']
        res = scale_to_res(tm['scale_denom'], srs)

        tl = tm['top_left']
        if previous_tl and tl != previous_tl:
            raise TileMatrixError('TileMatrixSet with non-uniform TopLeftCorners')
        previous_tl = tl

        bbox = tm_bbox(res, tl, tile_size, num_tiles)
        resolutions.append(res)

    return {
        'tile_size': tile_size,
        'resolutions': resolutions,
        'bbox': bbox,
        'srs': srs,
        'number_range': number != -1,
        'prefix': prefix,
        'name': tile_matrix_set['id'].replace(':', '_')
    }

def tm_bbox(res, tl, tile_size, num_tiles):
    br = (
        tl[0] - tile_size[1] * res * num_tiles[1],
        tl[1] + tile_size[0] * res * num_tiles[0],
    )
    return tuple(round(x, 8) for x in (tl[1], br[0], br[1], tl[0]))

def meters_per_unit(srs):
    if srs.is_latlong:
        return 20037508.342789244 / 180.0
    return 1.0

def scale_to_res(scale, srs):
    return scale * 0.28e-3 / meters_per_unit(srs)

if __name__ == '__main__':
    print make_mapproxy_grid(test_grid)
