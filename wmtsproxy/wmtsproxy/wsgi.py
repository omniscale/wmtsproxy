from __future__ import absolute_import

import os.path

from mapproxy import multiapp

import logging

from .csv import available_configs
from .config_writer import write_mapproxy_conf, mapproxy_config_from_csv
from .exceptions import CapabilitiesError, UserError, FeatureError, ServiceError, ConfigWriterError

log = logging.getLogger(__name__)

class ConfigLoader(multiapp.DirectoryConfLoader):

    def __init__(self, base_dir, base_file, suffix='.yaml', csv_file='/tmp/layers.csv'):
        super(ConfigLoader, self).__init__(base_dir, suffix='.yaml')
        self.base_file = base_file
        self.csv_file = csv_file

    def app_available(self, app_name):
        if app_name in self.available_apps():
            return True
        return False

    def available_apps(self):
        apps = super(ConfigLoader, self).available_apps()
        apps += available_configs(self.csv_file)

        return list(set(apps))

    def app_conf(self, app_name):
        conf_file = self.filename_from_app_name(app_name)

        if not self._is_conf_file(conf_file):
            try:
                mapproxy_conf = mapproxy_config_from_csv(app_name, self.base_file, csv_config_file=self.csv_file)

                write_mapproxy_conf(mapproxy_conf, os.path.join(self.base_dir, app_name + self.suffix))
                conf_file = self.filename_from_app_name(app_name)
            except (CapabilitiesError, UserError) as ex:
                log.warn(ex.system_msg)
                return None
            except (FeatureError, ServiceError, ConfigWriterError) as ex:
                log.warn(ex.system_msg, exc_info=1)
                return None
            except Exception as ex:
                log.exception(ex)
                return None
        return {'mapproxy_conf': conf_file}

def make_wsgi_app(configs_path, base_file, csv_file, allow_listing=True, debug=False):
    configs_path = os.path.abspath(configs_path)
    if not os.path.exists(configs_path):
        os.makedirs(configs_path)
    loader = ConfigLoader(configs_path, base_file=base_file, csv_file=csv_file)
    return multiapp.MultiMapProxy(loader, list_apps=allow_listing, debug=debug)
