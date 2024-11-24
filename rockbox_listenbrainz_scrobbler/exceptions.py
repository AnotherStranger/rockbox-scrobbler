class InvalidAuthTokenException(Exception):
    def __init__(self, message="Invalid token"):
        self.message = message


class InvalidSubmitListensPayloadException(Exception):
    def __init__(self, message="Invalid payload"):
        self.message = message
