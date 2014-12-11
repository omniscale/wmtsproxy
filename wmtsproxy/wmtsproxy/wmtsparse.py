import re
import sys

from xml.etree import ElementTree as etree

from mapproxy.util.ext.wmsparse.util import resolve_ns
from mapproxy.util.py import reraise_exception

from .exceptions import CapabilitiesError

class WMTSCapabilities(object):

    _default_namespace = 'http://www.opengis.net/wmts/1.0'
    _namespaces = {
        'xlink': 'http://www.w3.org/1999/xlink',
        'ows': 'http://www.opengis.net/ows/1.1',
        'none': ''
    }

    def __init__(self, tree):
        if tree.getroot().tag != '{http://www.opengis.net/wmts/1.0}Capabilities':
            raise CapabilitiesError('Not a WMTS capabilities document')
        self.tree = tree
        self._service = None
        self._layers = None
        self._matrix_sets = None
        self._operations = None

    def resolve_ns(self, xpath):
        return resolve_ns(xpath, self._namespaces, self._default_namespace)

    def find(self, tree, xpath):
        return tree.find(self.resolve_ns(xpath))

    def findall(self, tree, xpath):
        return tree.findall(self.resolve_ns(xpath))

    def findtext(self, tree, xpath):
        return tree.findtext(self.resolve_ns(xpath))

    def attrib(self, elem, name):
        try:
            return elem.attrib[self.resolve_ns(name)]
        except KeyError:
            return None

    @property
    def service(self):
        if self._service is not None:
            return self._service

        self._service = dict(
            title = self.findtext(self.tree, 'ows:ServiceIdentification/ows:Title'),
            service_type = self.findtext(self.tree, 'ows:ServiceIdentification/ows:ServiceType'),
            service_type_version = self.findtext(self.tree, 'ows:ServiceIdentification/ows:ServiceTypeVersion'),
            provider_name = self.findtext(self.tree, 'ows:ServiceProvider/ows:ProviderName'),
            provider_individual_name = self.findtext(self.tree, 'ows:ServiceProvider/ows:ServiceContact/ows:IndividualName')
        )
        elem = self.find(self.tree, 'ows:ServiceProvider/ows:ProviderSite')
        if elem is not None:
            self._service['provider_site'] = self.attrib(elem, 'xlink:href')

        return self._service

    @property
    def operations(self):
        if self._operations is not None:
            return self._operations

        self._operations = {}
        operation_elems = self.findall(self.tree, 'ows:OperationsMetadata/ows:Operation')
        for operation_elem in operation_elems:
            operation = self.attrib(operation_elem, 'none:name')
            self._operations[operation] = {}
            url_elems = self.findall(operation_elem, 'ows:DCP/ows:HTTP/ows:Get')
            for url_elem in url_elems:
                mode = self.findtext(url_elem, 'ows:Constraint/ows:AllowedValues/ows:Value')
                if mode in self._operations[operation]:
                    continue
                self._operations[operation][mode] = self.attrib(url_elem, 'xlink:href')

        return self._operations

    @property
    def matrix_sets(self):
        if self._matrix_sets is not None:
            return self._matrix_sets

        self._matrix_sets = {}
        tile_matrix_sets_elems = self.findall(self.tree, 'Contents/TileMatrixSet')
        for tile_matrix_sets_elem in tile_matrix_sets_elems:
            identifier = self.findtext(tile_matrix_sets_elem, 'ows:Identifier')
            supported_crs = self.findtext(tile_matrix_sets_elem, 'ows:SupportedCRS')

            tile_matrices = []
            tile_matrix_elems = self.findall(tile_matrix_sets_elem, 'TileMatrix')
            for tile_matrix_elem in tile_matrix_elems:
                tile_width = int(self.findtext(tile_matrix_elem, 'TileWidth'))
                tile_height = int(self.findtext(tile_matrix_elem, 'TileHeight'))
                matrix_width = int(self.findtext(tile_matrix_elem, 'MatrixWidth'))
                matrix_height = int(self.findtext(tile_matrix_elem, 'MatrixHeight'))
                tile_matrices.append(dict(
                    id = self.findtext(tile_matrix_elem, 'ows:Identifier'),
                    top_left = top_left_corner_to_coord(self.findtext(tile_matrix_elem, 'TopLeftCorner'), supported_crs),
                    tile_size = (tile_width, tile_height),
                    grid_size = (matrix_width, matrix_height),
                    scale_denom = float(self.findtext(tile_matrix_elem, 'ScaleDenominator'))
                ))
            self._matrix_sets[identifier] = {
                'id': identifier,
                'crs': supported_crs,
                'tile_matrices': tile_matrices
            }

        return self._matrix_sets

    @property
    def layers(self):
        if self._layers is not None:
            return self._layers

        self._layers = {}

        layer_elems = self.findall(self.tree, 'Contents/Layer')
        if len(layer_elems) == 0:
            raise CapabilitiesError('Document contains no layer')
        for layer_elem in layer_elems:
            layer_id = self.findtext(layer_elem, 'ows:Identifier')
            title = self.findtext(layer_elem, 'ows:Title')

            _bbox_lower_corner = [float(x) for x in self.findtext(layer_elem, 'ows:WGS84BoundingBox/ows:LowerCorner').split(' ')]
            _bbox_upper_corner = [float(x) for x in self.findtext(layer_elem, 'ows:WGS84BoundingBox/ows:UpperCorner').split(' ')]
            bbox = _bbox_lower_corner + _bbox_upper_corner

            formats = []
            format_elems = self.findall(layer_elem, 'Format')
            for format_elem in format_elems:
                formats.append(format_elem.text)

            info_formats = []
            info_format_elems = self.findall(layer_elem, 'InfoFormat')
            for info_format_elem in info_format_elems:
                info_formats.append(info_format_elem.text)

            styles = []
            default_style = None
            style_elems = self.findall(layer_elem, 'Style')
            for style_elem in style_elems:
                default = self.attrib(style_elem, 'none:isDefault') == 'true' or False
                style_title = self.findtext(style_elem, 'ows:Title')
                style_id = self.findtext(style_elem, 'ows:Identifier')
                _style = {
                    'id': style_id,
                    'title': style_title,
                    'default': default
                }

                styles.append(_style)
                if _style['default']:
                    default_style = _style

            dimensions = []
            dimension_elems = self.findall(layer_elem, 'Dimension')
            for dimension_elem in dimension_elems:
                dimensions.append({
                    'id': self.findtext(dimension_elem, 'ows:Identifier'),
                    'default': self.findtext(dimension_elem, 'Default'),
                    'current': self.findtext(dimension_elem, 'Current'),
                    'value': self.findtext(dimension_elem, 'Value')
                })

            matrix_sets = []
            matrix_set_elems = self.findall(layer_elem, 'TileMatrixSetLink')
            for matrix_set_elem in matrix_set_elems:
                matrix_set_identifier = self.findtext(matrix_set_elem, 'TileMatrixSet')
                if not matrix_set_identifier in self.matrix_sets.keys():
                    raise CapabilitiesError('Matrix set required by layer not defined in capabilities document')
                matrix_sets.append(self.matrix_sets[matrix_set_identifier])

            self._layers[layer_id] = {
                'title': title,
                'bbox': bbox,
                'formats': formats,
                'info_formats': info_formats,
                'matrix_sets': matrix_sets,
                'styles': styles,
                'default_style': default_style,
                'url_template': self._wmts_url_template(layer_elem, dimensions),
                'dimensions': dimensions
            }

        return self._layers

    def _exists_operation_mode(self, operation, mode):
        return self.operations and operation in self.operations.keys() and mode in self.operations[operation].keys()

    def _wmts_url_template(self, layer_elem, dimensions):
        url_template = None
        resource_elem = self.find(layer_elem, 'ResourceURL')

        if resource_elem is not None:
            url_template = self.attrib(resource_elem, 'none:template')
            url_template = url_template.replace('{Style}', '%(style)s')
            url_template = url_template.replace('{TileMatrixSet}', '%(tile_matrix_set)s')
            url_template = url_template.replace('{TileMatrix}', '%%(z)s')
            url_template = url_template.replace('{TileRow}', '%%(y)s')
            url_template = url_template.replace('{TileCol}', '%%(x)s')
            url_template = _replace_dimensions(url_template, dimensions)
        elif self._exists_operation_mode('GetTile', 'KVP'):
            url_template = self.operations['GetTile']['KVP']
            url_template += 'SERVICE=WMTS'
            url_template += '&REQUEST=GetTile'
            url_template += '&VERSION=1.0.0'
            url_template += '&LAYER=%(layer)s'
            url_template += '&TILEMATRIXSET=%(tile_matrix_set)s'
            url_template += '&TILEMATRIX=%%(z)s'
            url_template += '&TILEROW=%%(y)s'
            url_template += '&TILECOL=%%(x)s'
            url_template += '&FORMAT=%(format)s'

        return url_template

def _add_dimensions(url_template, dimensions):
    dimensions = ''
    for dimension in dimensions:
        dimensions += '/%%(%s)s' % dimension['id']
    return url_template.replace('%(dimensions)s', dimensions)

def _replace_dimensions(url_template, dimensions):
    for dimension in dimensions:
        dimension_re = re.compile(re.escape('{%s}' % dimension['id']), re.IGNORECASE)
        url_template = dimension_re.sub('%%(%s)s' % dimension['id'], url_template)
    return url_template

def top_left_corner_to_coord(top_left_corner, crs):
    coord = tuple(float(x) for x in top_left_corner.split(' '))
    if crs in [
        'CRS:84',
        'EPSG:900913',
        'EPSG:25831',
        'EPSG:25832',
        'EPSG:25833',
        'urn:ogc:def:crs:EPSG::900913',
        'urn:ogc:def:crs:EPSG::25831',
        'urn:ogc:def:crs:EPSG::25832',
        'urn:ogc:def:crs:EPSG::25833',
        'urn:ogc:def:crs:EPSG:6.18:3:900913',
        'urn:ogc:def:crs:EPSG:6.18:3:25831',
        'urn:ogc:def:crs:EPSG:6.18:3:25832',
        'urn:ogc:def:crs:EPSG:6.18:3:25833',
        'urn:ogc:def:crs:OGC:1.3:CRS84'
    ]:
        return (coord[1], coord[0])
    return coord

def parse_capabilities(fileobj):
    if isinstance(fileobj, basestring):
        fileobj = open(fileobj)

    try:
        tree = etree.parse(fileobj)
    except Exception as ex:
        reraise_exception(CapabilitiesError('Could not open capabilities document', ex.args[0]), sys.exc_info())

    return WMTSCapabilities(tree)
