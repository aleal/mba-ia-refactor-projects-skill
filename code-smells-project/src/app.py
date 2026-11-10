import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database.connection import get_db, get_readonly_db, init_db
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.admin_routes import build_admin_routes
from src.views.pedido_routes import build_pedido_routes
from src.views.produto_routes import build_produto_routes
from src.views.relatorio_routes import build_relatorio_routes
from src.views.sistema_routes import build_sistema_routes
from src.views.usuario_routes import build_usuario_routes


def create_app(settings=None):
    """Composition root: config, banco, models, controllers, rotas e handlers."""
    settings = settings or Settings()
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    init_db(app, admin_password=settings.SEED_ADMIN_PASSWORD)

    produto_model = ProdutoModel(get_db)
    usuario_model = UsuarioModel(get_db)
    pedido_model = PedidoModel(get_db)
    admin_model = AdminModel(get_db, get_readonly_db)
    notifier = NotificationService()

    app.register_blueprint(build_sistema_routes(
        SistemaController(produto_model, usuario_model, pedido_model, settings.APP_VERSION, settings.APP_ENV)
    ))
    app.register_blueprint(build_produto_routes(ProdutoController(produto_model)))
    app.register_blueprint(build_usuario_routes(UsuarioController(usuario_model)))
    app.register_blueprint(build_pedido_routes(PedidoController(pedido_model, usuario_model, notifier)))
    app.register_blueprint(build_relatorio_routes(RelatorioController(pedido_model)))
    app.register_blueprint(build_admin_routes(
        AdminController(admin_model, settings.ENABLE_ADMIN_QUERY, settings.ENABLE_ADMIN_RESET)
    ))

    register_error_handlers(app)
    return app
