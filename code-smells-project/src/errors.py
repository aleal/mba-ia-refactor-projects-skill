class AppError(Exception):
    """Erro de domínio; convertido em resposta HTTP apenas pelo handler central."""

    status_code = 400

    def __init__(self, message, status_code=None, sucesso=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        # Algumas respostas de erro da API original incluem "sucesso": false e outras não.
        self.sucesso = sucesso

    def to_dict(self):
        body = {"erro": self.message}
        if self.sucesso is not None:
            body["sucesso"] = self.sucesso
        return body


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404
