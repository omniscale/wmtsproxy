from ..grid import make_mapproxy_grid

from nose.tools import eq_

epsg4326_1km = {
    'crs': 'urn:ogc:def:crs:OGC:1.3:CRS84',
    'id': 'EPSG4326_1km',
    'tile_matrices': [
       {'grid_size': (2, 1),
        'id': '0',
        'scale_denom': 223632905.6114871,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (3, 2),
        'id': '1',
        'scale_denom': 111816452.8057436,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (5, 3),
        'id': '2',
        'scale_denom': 55908226.40287178,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (10, 5),
        'id': '3',
        'scale_denom': 27954113.20143589,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (20, 10),
        'id': '4',
        'scale_denom': 13977056.60071795,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (40, 20),
        'id': '5',
        'scale_denom': 6988528.300358973,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)},
       {'grid_size': (80, 40),
        'id': '6',
        'scale_denom': 3494264.150179486,
        'tile_size': (512, 512),
        'top_left': (90.0, -180.0)}]
}

class TestTileMatrixGrid(object):
    def test_nasa_wgs84_grid(self):
        g = make_mapproxy_grid(epsg4326_1km)
        eq_(g['name'], 'EPSG4326_1km')
        eq_(g['bbox'], (-180.0, -90.0, 180.0, 90.0))
        eq_(g['tile_size'], (512, 512))

        print g