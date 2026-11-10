from src.errors import ValidationError
from src.models.pedido_model import STATUS_VALIDOS

ITEM_INVALIDO = "Item inválido: produto_id e quantidade (inteiro positivo) são obrigatórios"


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_int(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ValidationError(ITEM_INVALIDO)
    for item in itens:
        if not isinstance(item, dict) or not _is_int(item.get("produto_id")):
            raise ValidationError(ITEM_INVALIDO)
        if not _is_int(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError(ITEM_INVALIDO)
    itens_limpos = [{"produto_id": item["produto_id"], "quantidade": item["quantidade"]} for item in itens]
    return usuario_id, itens_limpos


class PedidoController:
    def __init__(self, pedido_model, usuario_model, notifier):
        self.pedidos = pedido_model
        self.usuarios = usuario_model
        self.notifier = notifier

    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)
        if not self.usuarios.existe(usuario_id):
            raise ValidationError("Usuário não encontrado", sucesso=False)
        resultado = self.pedidos.criar(usuario_id, itens)
        self.notifier.pedido_criado(resultado["pedido_id"], usuario_id)
        return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201

    def listar_todos(self):
        return {"dados": self.pedidos.listar_todos(), "sucesso": True}, 200

    def listar_por_usuario(self, usuario_id):
        return {"dados": self.pedidos.listar_por_usuario(usuario_id), "sucesso": True}, 200

    def atualizar_status(self, pedido_id, dados):
        dados = dados if isinstance(dados, dict) else {}
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        self.pedidos.atualizar_status(pedido_id, novo_status)
        self.notifier.status_alterado(pedido_id, novo_status)
        return {"sucesso": True, "mensagem": "Status atualizado"}, 200
