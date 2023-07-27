class ConnectivityException(Exception):  # noqa: N818
    pass


class VLANHandlerException(ConnectivityException):
    pass


class RequestValidatorException(ConnectivityException):
    pass


class ApplyConnectivityException(ConnectivityException):
    pass
