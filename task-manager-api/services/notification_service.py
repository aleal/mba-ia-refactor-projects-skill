import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(frozen=True)
class EmailSettings:
    enabled: bool
    host: str
    port: int
    user: str
    password: str

    @classmethod
    def from_config(cls, config):
        return cls(
            enabled=config['NOTIFICATIONS_ENABLED'],
            host=config['SMTP_HOST'],
            port=config['SMTP_PORT'],
            user=config['SMTP_USER'],
            password=config['SMTP_PASSWORD'],
        )


class NotificationService:
    def __init__(self, settings, logger, smtp_factory=smtplib.SMTP):
        self._settings = settings
        self._logger = logger
        self._smtp_factory = smtp_factory

    def send_email(self, to, subject, body):
        if not self._settings.enabled:
            self._logger.info('envio de e-mail desligado; notificação descartada: %s', subject)
            return False
        message = EmailMessage()
        message['From'] = self._settings.user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with self._smtp_factory(self._settings.host, self._settings.port, timeout=10) as server:
                server.starttls()
                server.login(self._settings.user, self._settings.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            self._logger.exception('falha ao enviar e-mail: %s', subject)
            return False
        self._logger.info('e-mail enviado: %s', subject)
        return True

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        return self.send_email(user.email, subject, body)
