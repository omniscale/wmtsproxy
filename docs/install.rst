Installation
============

WMTSProxy can be installed like other Python application.
E.g. ``pip install path\to\wmtsproxy``, or you can create packages with ``python setup.py sdist``, etc.


Both services are WSGI applications.


The WSGI configuration for ``wmtsproxy`` should look like:
::

    import os
    here = os.path.abspath(os.path.dirname(__file__))
    from wmtsproxy.wsgi import make_wsgi_app

    application = make_wsgi_app(
        configs_path=os.path.join(here, 'tmp_configs'),
        base_file=os.path.join(here, 'mapproxy_base.yaml'),
        csv_file=os.path.join(here, 'services.csv'))


The WSGI configuration for ``wmtsproxy_restapi`` should look like:
::
    import os
    here = os.path.abspath(os.path.dirname(__file__))
    from wmtsproxy_restapi.app import create_app, DefaultConfig

    class Config(DefaultConfig):
        CSV_FILE = os.path.join(here, 'services.csv')

    application = create_app(Config)