class AppExceptionCase(Exception):
    def __init__(self, status_code: int, context: dict | None):
        self.exception_case = self.__class__.__name__
        self.status_code = status_code
        self.context = context

    def __str__(self):
        return f"<AppException {self.exception_case} status_code={self.status_code}>"


class AppException:
    class DatabaseConnectionFailed(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 503
            AppExceptionCase.__init__(self, status_code, context)

    class APIKeyInvalid(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, context)

    class TokenExpired(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, context)

    class TokenInvalid(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 401
            AppExceptionCase.__init__(self, status_code, context)

    class DocumentCreationFailed(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, context)

    class DocumentNotFound(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, context)

    class ChunkCreationFailed(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, context)

    class ChunkNotFound(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, context)

    class IntegrationAlreadyExists(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 409
            AppExceptionCase.__init__(self, status_code, context)

    class IntegrationNotFound(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 404
            AppExceptionCase.__init__(self, status_code, context)

    class IntegrationInvalid(AppExceptionCase):
        def __init__(self, context: dict | None = None):
            status_code = 500
            AppExceptionCase.__init__(self, status_code, context)
