class WMTSProxyError(Exception):
    def __init__(self, user_msg, system_msg=None):
        Exception.__init__(self, user_msg)
        self.user_msg = user_msg
        self._system_msg = system_msg

    @property
    def system_msg(self):
        if self._system_msg is None:
            return self.user_msg
        return self._system_msg

class CapabilitiesError(WMTSProxyError):
    pass

class ConfigWriterError(WMTSProxyError):
    pass

class TileMatrixError(WMTSProxyError):
    pass

class FeatureError(WMTSProxyError):
    pass

class ServiceError(WMTSProxyError):
    pass

class UserError(WMTSProxyError):
    pass
