from loguru import logger

from .app_exceptions import AppExceptionCase


class ServiceResult(object):
    def __init__(self, value_or_exception):
        if isinstance(value_or_exception, AppExceptionCase):
            self.success = False
            self.exception_case = value_or_exception.exception_case
            self.status_code = value_or_exception.status_code
        else:
            self.success = True
            self.exception_case = None
            self.status_code = None
        self.value = value_or_exception

    def __str__(self):
        if self.success:
            return "[Success]"
        return f'[Exception] "{self.exception_case}"'

    def __repr__(self):
        if self.success:
            return "<ServiceResult Success>"
        return f"<ServiceResult AppException {self.exception_case}>"

    def __enter__(self):
        return self.value

    def __exit__(self, *kwargs):
        pass


def handle_result(result: ServiceResult):
    if not result.success:
        with result as exception:
            logger.error(exception)
            raise exception
    with result as result:
        return result