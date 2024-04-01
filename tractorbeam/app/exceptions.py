class AppExceptionCase(Exception):
    def __init__(self, status_code: int, message: str | None):
        self.exception_case = self.__class__.__name__
        self.status_code = status_code
        self.message = message

    def __repr__(self):
        return f'<AppException.{self.exception_case} message="{self.message}>"'


class AppException:
    class DatabaseConnectionFailed(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 503
            AppExceptionCase.__init__(self, status_code, message)

    class APIKeyInvalid(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, message)

    class TokenExpired(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, message)

    class TokenInvalid(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, message)

    class DocumentCreationFailed(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, message)

    class DocumentNotFound(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, message)

    class ChunkCreationFailed(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, message)

    class ChunkNotFound(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, message)

    class IntegrationAlreadyExists(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 409
            AppExceptionCase.__init__(self, status_code, message)

    class IntegrationNotFound(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, message)

    class IntegrationMisconfigured(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, message)

    class ConnectionCreationFailed(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, message)

    class ConnectionInvalid(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 422
            AppExceptionCase.__init__(self, status_code, message)

    class ConnectionNotFound(AppExceptionCase):
        def __init__(self, message: str | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, message)
