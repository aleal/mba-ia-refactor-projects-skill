import logging

from src.models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO


class NotificationService:
    """Notificações de pedido. Por ora só registra em log; um envio real entra aqui sem tocar nos controllers."""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def _enviar(self, canal, mensagem, *args):
        try:
            self.logger.info("[%s] " + mensagem, canal, *args)
        except Exception:  # falha de notificação nunca derruba o fluxo do pedido
            self.logger.exception("falha ao enviar notificação via %s", canal)

    def pedido_criado(self, pedido_id, usuario_id):
        self._enviar("email", "pedido %s criado para usuario %s", pedido_id, usuario_id)
        self._enviar("sms", "pedido %s recebido", pedido_id)
        self._enviar("push", "novo pedido %s recebido pelo sistema", pedido_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_APROVADO:
            self._enviar("interno", "pedido %s aprovado, preparar envio", pedido_id)
        elif novo_status == STATUS_CANCELADO:
            self._enviar("interno", "pedido %s cancelado, devolver estoque", pedido_id)
