def is_supported_srs(srs):
    if not srs.startswith('EPSG'):
        return False
    return True