import logging

from src.errors import NotFoundError, ValidationError
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN

logger = logging.getLogger(__name__)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validar_produto(dados):
    """Validação única de criar e atualizar; mensagens iguais às da API original."""
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser um número inteiro")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def _parse_preco(args, nome):
    valor = args.get(nome)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome + " inválido")


class ProdutoController:
    def __init__(self, produto_model):
        self.produtos = produto_model

    def listar(self):
        produtos = self.produtos.listar()
        logger.info("listando %d produtos", len(produtos))
        return {"dados": produtos, "sucesso": True}, 200

    def buscar_por_id(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return {"dados": produto, "sucesso": True}, 200

    def buscar(self, args):
        resultados = self.produtos.buscar(
            args.get("q", ""),
            args.get("categoria"),
            _parse_preco(args, "preco_min"),
            _parse_preco(args, "preco_max"),
        )
        return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200

    def criar(self, dados):
        produto = validar_produto(dados)
        produto_id = self.produtos.criar(**produto)
        logger.info("produto criado id=%s", produto_id)
        return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201

    def atualizar(self, produto_id, dados):
        if self.produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")
        produto = validar_produto(dados)
        self.produtos.atualizar(produto_id, **produto)
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200

    def deletar(self, produto_id):
        if self.produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")
        self.produtos.deletar(produto_id)
        logger.info("produto deletado id=%s", produto_id)
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200
