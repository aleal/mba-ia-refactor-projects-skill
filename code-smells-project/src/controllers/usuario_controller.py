import logging

from src.errors import NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


class UsuarioController:
    def __init__(self, usuario_model):
        self.usuarios = usuario_model

    def listar(self):
        return {"dados": self.usuarios.listar(), "sucesso": True}, 200

    def buscar_por_id(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return {"dados": usuario, "sucesso": True}, 200

    def criar(self, dados):
        if not dados or not isinstance(dados, dict):
            raise ValidationError("Dados inválidos")
        nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        usuario_id = self.usuarios.criar(nome, email, senha)
        logger.info("usuario criado id=%s", usuario_id)
        return {"dados": {"id": usuario_id}, "sucesso": True}, 201

    def login(self, dados):
        dados = dados if isinstance(dados, dict) else {}
        email, senha = _texto(dados, "email"), _texto(dados, "senha")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        usuario = self.usuarios.autenticar(email, senha)
        if usuario is None:
            logger.info("login falhou")
            raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
        logger.info("login bem-sucedido usuario_id=%s", usuario["id"])
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
