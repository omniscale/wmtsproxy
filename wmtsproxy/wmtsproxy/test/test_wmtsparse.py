import os

from ..wmtsparse import parse_capabilities

from nose.tools import eq_

def local_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)

class TestWMTS100(object):
    def test_parse_service(self):
        cap = parse_capabilities(local_filename('data/wmts-v2.suite.opengeo.org-100.xml'))
        service = cap.service

        eq_(service['title'], 'Web Map Tile Service - GeoWebCache')
        eq_(service['service_type'], 'OGC WMTS')
        eq_(service['service_type_version'], '1.0.0')
        eq_(service['provider_name'], 'http://v2.suite.opengeo.org/geoserver/gwc/service/wmts')
        eq_(service['provider_site'], 'http://v2.suite.opengeo.org/geoserver/gwc/service/wmts')
        eq_(service['provider_individual_name'], 'GeoWebCache User')

    def test_parse_operations(self):
        cap = parse_capabilities(local_filename('data/wmts-v2.suite.opengeo.org-100.xml'))
        operations = cap.operations

        eq_(len(operations), 3)

        for key in ['GetCapabilities', 'GetTile', 'GetFeatureInfo']:
            assert(key in operations.keys())

        eq_(len(operations['GetTile']), 1)
        assert('KVP' in operations['GetTile'].keys())

        eq_(operations['GetTile']['KVP'], 'http://v2.suite.opengeo.org/geoserver/gwc/service/wmts?')

    def test_parse_tile_matrix_sets(self):
        cap = parse_capabilities(local_filename('data/wmts-v2.suite.opengeo.org-100.xml'))
        matrix_sets = cap.matrix_sets

        eq_(len(matrix_sets), 5)

        for key in ['GlobalCRS84Scale', 'EPSG:4326', 'GoogleCRS84Quad', 'EPSG:900913', 'GlobalCRS84Pixel']:
            assert(key in matrix_sets.keys())

        test_matrix_set = matrix_sets['EPSG:4326']

        eq_(test_matrix_set['crs'], 'urn:ogc:def:crs:EPSG::4326')
        eq_(len(test_matrix_set['tile_matrices']), 22)

        eq_(test_matrix_set['tile_matrices'][0]['id'], 'EPSG:4326:0')
        eq_(test_matrix_set['tile_matrices'][0]['top_left'], (90.0, -180.0))
        eq_(test_matrix_set['tile_matrices'][0]['tile_size'], (256, 256))
        eq_(test_matrix_set['tile_matrices'][0]['grid_size'], (2, 1))
        eq_(test_matrix_set['tile_matrices'][0]['scale_denom'], 279541132.0143589)

        eq_(test_matrix_set['tile_matrices'][6]['id'], 'EPSG:4326:6')
        eq_(test_matrix_set['tile_matrices'][6]['top_left'], (90.0, -180.0))
        eq_(test_matrix_set['tile_matrices'][6]['tile_size'], (256, 256))
        eq_(test_matrix_set['tile_matrices'][6]['grid_size'], (128, 64))
        eq_(test_matrix_set['tile_matrices'][6]['scale_denom'], 4367830.1877243575)

    def test_parse_layers(self):
        cap = parse_capabilities(local_filename('data/wmts-v2.suite.opengeo.org-100.xml'))
        layers = cap.layers

        eq_(len(layers), 3)

        for key in ['opengeo:geonames', 'world', 'medford']:
            assert key in layers.keys()

        test_layer = layers['world']
        eq_(test_layer['title'], 'world')
        eq_(test_layer['bbox'], [-180.0, -90.0, 180.0, 83.624])

        eq_(len(test_layer['formats']), 2)
        for key in ['image/png', 'image/jpeg']:
            assert key in test_layer['formats']

        eq_(len(test_layer['info_formats']), 3)
        for key in ['text/plain', 'text/html', 'application/vnd.ogc.gml']:
            assert key in test_layer['info_formats']

        eq_(len(test_layer['matrix_sets']), 2)
        for matrix_set in test_layer['matrix_sets']:
            assert(isinstance(matrix_set, dict))

        eq_(test_layer['matrix_sets'][0]['crs'], 'urn:ogc:def:crs:EPSG::4326')

        eq_(test_layer['url_template'], 'http://v2.suite.opengeo.org/geoserver/gwc/service/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=%(layer)s&TILEMATRIXSET=%(tile_matrix_set)s&TILEMATRIX=%%(z)s&TILEROW=%%(y)s&TILECOL=%%(x)s&FORMAT=%(format)s')

    def test_parse_nasa_layer(self):
        cap = parse_capabilities(local_filename('data/wmts-map1.vis.earthdata.nasa.gov.xml'))
        test_layer = cap.layers['AIRS_CO_Total_Column_Day']

        eq_(test_layer['title'], 'AIRS_CO_Total_Column_Day')

        eq_(len(test_layer['styles']), 1)
        eq_(test_layer['styles'][0]['id'], 'default')
        eq_(test_layer['styles'][0]['title'], 'default')
        eq_(test_layer['styles'][0]['default'], True)

        eq_(test_layer['default_style']['id'], 'default')
        eq_(test_layer['default_style']['title'], 'default')
        eq_(test_layer['default_style']['default'], True)

        eq_(test_layer['url_template'], 'http://map1.vis.earthdata.nasa.gov/wmts-geo/AIRS_CO_Total_Column_Day/default/%(time)s/%(tile_matrix_set)s/%%(z)s/%%(y)s/%%(x)s.png')

        eq_(len(test_layer['dimensions']), 1)

        test_dimension = test_layer['dimensions'][0]

        eq_(len(test_dimension), 4)
        for key in ['id', 'default', 'current', 'value']:
            assert(key in test_dimension.keys())

        eq_(test_dimension['id'], 'time')
        eq_(test_dimension['default'], '2014-03-31')
        eq_(test_dimension['current'], 'false')
        eq_(test_dimension['value'], '2012-05-08/2014-03-31/P1D')

class TestWMTS100BaseMapAT(object):
    def test_parse_service(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at.xml'))
        service = cap.service

        eq_(service['title'], 'Basemap.at')
        eq_(service['service_type'], 'Basemap.at WMTS')
        eq_(service['service_type_version'], '1.0.0')
        eq_(service['provider_name'], 'City of Vienna')
        eq_(service['provider_site'], 'http://www.wien.gv.at/viennagis')

    def test_parse_operations(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at.xml'))
        operations = cap.operations

        eq_(len(operations), 2)

        for key in ['GetCapabilities', 'GetTile']:
            assert(key in operations.keys())

        eq_(len(operations['GetTile']), 1)
        assert('RESTful' in operations['GetTile'].keys())
        eq_(operations['GetTile']['RESTful'], 'http://maps.wien.gv.at/basemap')

    def test_parse_tile_matrix_sets(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at.xml'))
        matrix_sets = cap.matrix_sets

        eq_(len(matrix_sets), 1)

        assert('google3857' in matrix_sets.keys())

        test_matrix_set = matrix_sets['google3857']

        eq_(test_matrix_set['crs'], 'urn:ogc:def:crs:EPSG:6.18:3:3857')
        eq_(len(test_matrix_set['tile_matrices']), 20)

        test_tile_matrix = test_matrix_set['tile_matrices'][0]
        eq_(test_tile_matrix['id'], '0')
        eq_(test_tile_matrix['top_left'], (-20037508.3428, 20037508.3428))
        eq_(test_tile_matrix['tile_size'], (256, 256))
        eq_(test_tile_matrix['grid_size'], (1, 1))
        eq_(test_tile_matrix['scale_denom'], 559082264.029)

        test_tile_matrix = test_matrix_set['tile_matrices'][9]
        eq_(test_tile_matrix['id'], '9')
        eq_(test_tile_matrix['top_left'], (-20037508.3428, 20037508.3428))
        eq_(test_tile_matrix['tile_size'], (256, 256))
        eq_(test_tile_matrix['grid_size'], (512, 512))
        eq_(test_tile_matrix['scale_denom'], 1091957.54693)

    def test_parse_layer(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at.xml'))
        layers = cap.layers

        eq_(len(layers), 1)
        assert 'geolandbasemap' in layers.keys()

        test_layer = layers['geolandbasemap']
        eq_(test_layer['title'], 'Geoland Basemap')
        eq_(test_layer['bbox'], [9.3, 46.0, 17.6, 49.2])

        eq_(len(test_layer['styles']), 1)
        eq_(test_layer['styles'][0]['id'], 'normal')
        eq_(test_layer['styles'][0]['default'], True)

        eq_(test_layer['default_style']['id'], 'normal')
        eq_(test_layer['default_style']['default'], True)

        eq_(len(test_layer['formats']), 1)
        assert 'image/jpeg' in test_layer['formats']

        eq_(len(test_layer['matrix_sets']), 1)
        for matrix_set in test_layer['matrix_sets']:
            assert(isinstance(matrix_set, dict))

        eq_(test_layer['matrix_sets'][0]['crs'], 'urn:ogc:def:crs:EPSG:6.18:3:3857')

        eq_(test_layer['url_template'], 'http://maps1.wien.gv.at/basemap/geolandbasemap/%(style)s/%(tile_matrix_set)s/%%(z)s/%%(y)s/%%(x)s.jpeg')

class TestWMTS100BaseMapATArcmap(object):
    def test_parse_service(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at-arcmap.xml'))
        service = cap.service

        eq_(service['title'], 'basemap.at')
        eq_(service['service_type'], 'Basemap.at WMTS')
        eq_(service['service_type_version'], '1.0.0')
        eq_(service['provider_name'], 'City of Vienna')
        eq_(service['provider_site'], 'http://www.wien.gv.at/viennagis')

    def test_parse_operations(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at-arcmap.xml'))
        operations = cap.operations

        eq_(len(operations), 2)

        for key in ['GetCapabilities', 'GetTile']:
            assert(key in operations.keys())

        eq_(len(operations['GetTile']), 1)
        assert('RESTful' in operations['GetTile'].keys())
        eq_(operations['GetTile']['RESTful'], 'http://maps.wien.gv.at/basemap')

    def test_parse_tile_matrix_sets(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at-arcmap.xml'))
        matrix_sets = cap.matrix_sets

        eq_(len(matrix_sets), 1)

        assert('google3857' in matrix_sets.keys())

        test_matrix_set = matrix_sets['google3857']

        eq_(test_matrix_set['crs'], 'urn:ogc:def:crs:EPSG:6.18:3:3857')
        eq_(len(test_matrix_set['tile_matrices']), 20)

        test_tile_matrix = test_matrix_set['tile_matrices'][0]
        eq_(test_tile_matrix['id'], '0')
        eq_(test_tile_matrix['top_left'], (-20037508.3428, 20037508.3428))
        eq_(test_tile_matrix['tile_size'], (256, 256))
        eq_(test_tile_matrix['grid_size'], (1, 1))
        eq_(test_tile_matrix['scale_denom'], 5.590811458640437E8)

        test_tile_matrix = test_matrix_set['tile_matrices'][9]
        eq_(test_tile_matrix['id'], '9')
        eq_(test_tile_matrix['top_left'], (-20037508.3428, 20037508.3428))
        eq_(test_tile_matrix['tile_size'], (256, 256))
        eq_(test_tile_matrix['grid_size'], (512, 512))
        eq_(test_tile_matrix['scale_denom'], 1091955.3630154685)

    def test_parse_layer(self):
        cap = parse_capabilities(local_filename('data/wmts-www.basemap.at-arcmap.xml'))
        layers = cap.layers

        eq_(len(layers), 1)
        assert 'geolandbasemap' in layers.keys()

        test_layer = layers['geolandbasemap']
        eq_(test_layer['title'], 'Geoland Basemap')
        eq_(test_layer['bbox'], [9.3, 46.0, 17.6, 49.2])

        eq_(len(test_layer['styles']), 1)
        eq_(test_layer['styles'][0]['id'], 'normal')
        eq_(test_layer['styles'][0]['default'], True)

        eq_(test_layer['default_style']['id'], 'normal')
        eq_(test_layer['default_style']['default'], True)

        eq_(len(test_layer['formats']), 1)
        assert 'image/jpeg' in test_layer['formats']

        eq_(len(test_layer['matrix_sets']), 1)
        for matrix_set in test_layer['matrix_sets']:
            assert(isinstance(matrix_set, dict))

        eq_(test_layer['matrix_sets'][0]['crs'], 'urn:ogc:def:crs:EPSG:6.18:3:3857')

        eq_(test_layer['url_template'], 'http://maps1.wien.gv.at/basemap/geolandbasemap/%(style)s/%(tile_matrix_set)s/%%(z)s/%%(y)s/%%(x)s.jpeg')
