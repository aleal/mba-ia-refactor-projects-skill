from itsdangerous import BadSignature, URLSafeTimedSerializer


class TokenService:
    """Tokens de acesso assinados com SECRET_KEY e com expiração."""

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age

    def issue(self, user):
        return self._serializer.dumps({'uid': user.id})

    def verify(self, token):
        """Devolve o id do usuário do token, ou None se inválido/expirado."""
        try:
            data = self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:  # inclui SignatureExpired
            return None
        return data.get('uid') if isinstance(data, dict) else None
