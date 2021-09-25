class ExceptionAPI(Exception):
    default_message = None
    default_code = 'invalid'

    def __init__(self, message=None):
        if message is None:
            message = self.default_message

        super().__init__(message)


class AuthenticationFailed(ExceptionAPI):
    default_code = 'authentication_failed'


class WrongUsage(ExceptionAPI):
    """
    internal exception
    """
    default_code = "wrong_usage"
    default_message = "Wrong usage, check your code!."
