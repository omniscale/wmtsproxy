import logging
from functools import wraps
from flask import Flask, request, jsonify, current_app

from wmtsproxy.capabilities import add_wms_layer, add_wmts_layer, cap_dict
from wmtsproxy.exceptions import CapabilitiesError, UserError, FeatureError, ServiceError

log = logging.getLogger(__name__)
app = Flask(__name__)

class DefaultConfig(object):
    CSV_FILE = './services.csv'

def create_app(config=None):
    app.config.from_object(DefaultConfig())

    if config is not None:
        app.config.from_object(config)

    return app

def json_error_response(message, status=500):
    resp = jsonify({'error': message})
    resp.status_code = status
    return resp

def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

@app.route('/check')
@jsonp
def list_layers():
    cap_url = request.args.get('url')
    if cap_url is None:
        return json_error_response('Missing url parameter for capabilities', status=400)

    try:
        cap = cap_dict(cap_url)
        return jsonify(cap)
    except (CapabilitiesError, UserError) as ex:
        log.debug(ex.system_msg)
        return json_error_response(ex.user_msg, status=400)
    except (FeatureError, ServiceError) as ex:
        log.debug(ex.system_msg, exc_info=1)
        return json_error_response(ex.user_msg)
    except Exception as ex:
        log.exception(ex)
        return json_error_response('internal server error')

@app.route('/add')
@jsonp
def add_layer():
    cap_type = request.args.get('type')
    if cap_type not in ('wmts', 'wms'):
        return json_error_response('Missing/unknown capabilities type', status=400)

    cap_url = request.args.get('url')
    layer_name = request.args.get('layer')

    if cap_url is None:
        return json_error_response('Missing url parameter for capabilities', status=400)

    if layer_name is None:
        return json_error_response('Missing layer parameter', status=400)

    if cap_type == 'wms':
        system_id = request.args.get('srs')
        if not system_id:
            return json_error_response('Missing srs parameter', status=400)
    if cap_type == 'wmts':
        system_id = request.args.get('matrix_set')
        if not system_id:
            return json_error_response('Missing matrix_set parameter', status=400)

    try:
        if cap_type == 'wmts':
            dimensions = {}
            time = request.args.get('time')
            if time:
                dimensions['time'] = time
            service_name = add_wmts_layer(cap_url, layer_name=layer_name, matrix_set=system_id,
                csv_config_file=app.config.get('CSV_FILE'),
                dimensions=dimensions)
        else:
            service_name = add_wms_layer(cap_url, layer_name=layer_name, srs=system_id, csv_config_file=app.config.get('CSV_FILE'))
        return jsonify({'mapproxy_id': service_name})
    except (CapabilitiesError, UserError) as ex:
        log.debug(ex.system_msg)
        return json_error_response(ex.user_msg)
    except (FeatureError, ServiceError) as ex:
        log.debug(ex.system_msg, exc_info=1)
        return json_error_response(ex.user_msg)
    except Exception as ex:
        log.exception(ex)
        return json_error_response('internal server error')

