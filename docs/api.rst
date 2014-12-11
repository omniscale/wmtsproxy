Admin API
=========

The WMTSProxy comes with a simple HTTP API.

All endpoitns support JSONP with the `callback` parameter.


The following endpoints are available:

`/check`
--------

Check if the URL of a capabilities document is valid and if the document is parsable.
Returns a JSON document with a list of all available layers.
WMTS layers will contain the MatrixSets that are available for that layer.
WMS layers will contain the SRS that are available for that layer. Preferred projections (EPSG:3857, EPSG:900913 and EPSG:4326) are listed first,
other projections appear in the same order as in the capabilities document.

The `/check` endpoint requires a GET request with a `url` parameter with the complete capabilities URL.

Example for WMS::

    curl 'http://localhost:9091/check?url=http://osm.omniscale.net/proxy/service?request=GetCapabilities'
    {
      "layers": [
        {
          "llbbox": [
            -180.0,
            -85.0511287798,
            180.0,
            85.0511287798
          ],
          "name": "osm",
          "srs": [
            "EPSG:3857",
            "EPSG:900913",
            "EPSG:4326",
            "EPSG:31467",
            "EPSG:31466",
            "EPSG:25832",
            "EPSG:25831",
            "EPSG:25833",
            "EPSG:31468",
            "CRS:84",
            "EPSG:4258"
          ],
          "title": "OpenStreetMap (complete map)"
        },
        {
          "llbbox": [
            -180.0,
            -85.0511287798,
            180.0,
            85.0511287798
          ],
          "name": "osm_roads",
          "srs": [
            "EPSG:3857",
            "EPSG:900913",
            "EPSG:4326",
            "EPSG:31467",
            "EPSG:31466",
            "EPSG:25832",
            "EPSG:25831",
            "EPSG:25833",
            "EPSG:31468",
            "CRS:84",
            "EPSG:4258"
          ],
          "title": "OpenStreetMap (streets only)"
        }
      ],
      "title": "Omniscale OpenStreetMap WMS",
      "type": "wms"
    }


Example for WMTS::

    curl 'http://localhost:9091/check?url=http://map1.vis.earthdata.nasa.gov/wmts-geo/1.0.0/WMTSCapabilities.xml'
    {
      "layers": [
        {
          "dimensions": {
            "time": {
              "default": "2014-05-09",
              "value": "2012-05-08/2014-05-09/P1D"
            }
          },
          "llbbox": [
            -180.0,
            -90.0,
            180.0,
            90.0
          ],
          "matrix_sets": [
            "EPSG4326_250m"
          ],
          "name": "MODIS_Aqua_CorrectedReflectance_TrueColor",
          "title": "MODIS_Aqua_CorrectedReflectance_TrueColor"
        },
        {
          "dimensions": {
            "time": {
              "default": "2014-05-09",
              "value": "2012-05-08/2014-05-09/P1D"
            }
          },
          "llbbox": [
            -180.0,
            -90.0,
            180.0,
            90.0
          ],
          "matrix_sets": [
            "EPSG4326_500m"
          ],
          "name": "MODIS_Terra_SurfaceReflectance_Bands721",
          "title": "MODIS_Terra_SurfaceReflectance_Bands721"
        },
      [...]
      ],
      "title": "NASA Global Imagery Browse Services for EOSDIS",
      "type": "wmts"
    }


`/add`
------

Register a new service and layer. Returns a JSON document with the name of the new service (`mapproxy_id`).
You can access the new service at `http://localhost:9090/<mapproxy_id>/wmts/1.0.0/WMTSCapabilities.xml`

The `/add` endpoint requires a GET request with a `url` parameter with the complete capabilities URL and a `layer` parameter with the layer name and a `type` parameter with `wms` or `wmts`.

WMTS services also require a `matrix_set` parameter with the selected TileMatrix.
WMS services also require an `srs` parameter with the selected SRS.

Example for WMS::

    curl 'http://localhost:9091/add?type=wms&url=http://osm.omniscale.net/proxy/service?request=GetCapabilities&layer=osm&srs=EPSG:3857'
    {
        "mapproxy_id": "osm_omniscale_net_osm_EPSG_3857"
    }


Example for WMTS::

    curl 'http://localhost:9091/add?type=wmts&url=http://map1.vis.earthdata.nasa.gov/wmts-geo/1.0.0/WMTSCapabilities.xml&layer=MODIS_Terra_SurfaceReflectance_Bands143&matrix_set=EPSG4326_500m'
    {
        "mapproxy_id": "map1_vis_earthdata_nasa_gov_MODIS_Terra_SurfaceReflectance_Bands143_EPSG4326_500m"
    }


WMTS services also support time dimensions. WMTSProxy will use the `default` value of a dimension if no explicit value is set. This default value is interpreted every time the MapProxy configuration is re-created. You can create a service with an explicit value as follows::

    curl 'http://localhost:9091/add?type=wmts&url=http://map1.vis.earthdata.nasa.gov/wmts-geo/1.0.0/WMTSCapabilities.xml&layer=MODIS_Terra_SurfaceReflectance_Bands143&matrix_set=EPSG4326_500m&time=2014-04-01'
    {
        "mapproxy_id": "map1_vis_earthdata_nasa_gov_MODIS_Terra_SurfaceReflectance_Bands143_EPSG4326_500m_time_2014-04-01"
    }

