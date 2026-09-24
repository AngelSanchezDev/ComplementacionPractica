"""Errores de la capa de Modelo, compartidos por todas las entidades."""


class APIError(Exception):
    def __init__(self, message: str, code: str = "ERR_UNKNOWN"):
        super().__init__(message)
        self.code = code


class LoginError(APIError):
    def __init__(self, message: str, code: str = "ERR_LOGIN"):
        super().__init__(message, code)


class ScoreError(APIError):
    def __init__(self, message: str, code: str = "ERR_SCORE"):
        super().__init__(message, code)


class ValidationError(APIError):
    def __init__(self, message: str, code: str = "ERR_VALIDATION"):
        super().__init__(message, code)
