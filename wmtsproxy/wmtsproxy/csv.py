from __future__ import absolute_import

import time
import csv
import re
from cStringIO import StringIO
from urlparse import urlparse
from collections import namedtuple

from .exceptions import ServiceError

from mapproxy.util.lock import FileLock
from mapproxy.util.fs import write_atomic


fieldnames = ('id', 'type', 'url', 'layer_name', 'system_id', 'dimensions', 'timestamp')
record = namedtuple('record', fieldnames)


def serialize_dimensions(dims):
    """
    >>> serialize_dimensions({})
    ""
    >>> serialize_dimensions({'time': 'foo', 'eleveation': '100m'})
    "elevation=100m,time=foo"
    """
    if not dims:
        return ""
    return ','.join(k + '=' + dims[k] for k in sorted(dims.keys()))

def unserialize_dimensions(dims):
    """
    >>> unserialize_dimensions("")
    {}
    >>> unserialize_dimensions("time=foo,elevation=100m")
    {'elevation': '100m', 'time', 'foo'}
    """
    if not dims:
        return {}
    return dict(kv.split('=', 1) for kv in dims.split(','))

def read_csv(filename):
    records = {}
    with open(filename, 'rb') as f:
        csv_reader = csv.DictReader(f, fieldnames=fieldnames)
        for row in csv_reader:
            records[row['id']] = record(**row)
    return records


def write_csv(filename, records):
    buf = StringIO()
    csv_writer = csv.writer(buf)
    for id, rec in records.iteritems():
        csv_writer.writerow(list(rec))

    buf.seek(0)
    write_atomic(filename, buf.read())

def to_csv(csv_config_file, cap_type, cap_url, layer_name, system_id, dimensions=None):
    dimensions = serialize_dimensions(dimensions)

    id = urlparse(cap_url).netloc + '_' + layer_name + '_' + system_id
    if dimensions:
        id += '_' + dimensions

    id = re.sub('[^A-Za-z0-9-_]', '_', id)

    with FileLock(csv_config_file + '.lck'):
        records = read_csv(csv_config_file)
        records[id] = (id, cap_type, cap_url, layer_name, system_id, dimensions, time.time())
        write_csv(csv_config_file, records)

    return id

def from_csv(id, csv_config_file):
    with open(csv_config_file, 'rb') as f:
        csv_reader = csv.DictReader(f, fieldnames=fieldnames)
        for row in csv_reader:
            if row['id'] == id:
                ts = row['timestamp']
                if ts:
                    row['timestamp'] = float(ts)
                else:
                    row['timestamp'] = 0
                return record(**row)
    raise ServiceError('No configuration for "%s" found' % id)

def available_configs(csv_config_file):
    configs = []
    with open(csv_config_file, 'rb') as f:
        csv_reader = csv.DictReader(f, fieldnames=fieldnames)
        for row in csv_reader:
            configs.append(row['id'])
    return configs
