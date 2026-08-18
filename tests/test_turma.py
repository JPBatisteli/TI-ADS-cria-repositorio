import pytest

from app.models.campus import CAMPI
from app.models.disciplina import Disciplina
from app.models.turma import (
    CODIGOS_POR_TURMA,
    codigo_valido,
    listar_codigos,
    listar_disciplinas,
)

# Disciplinas ofertadas em cada campus, escritas de forma independente do cadastro para
# que uma alteração acidental nele seja detectada.
#
# PENDENTE: os códigos das turmas de ADS ainda não foram informados, por isso o cadastro
# tem as disciplinas sem nenhuma turma. Quando os códigos chegarem, este espelho passa a
# conter também os códigos, como no projeto de origem.
DISCIPLINAS_ESPERADAS = ["TIAW", "TIAPN", "TIDAI", "TIAM", "TIAI"]

CAMPI_ESPERADOS = ["pbe", "pco"]


class TestCatalogo:

    @pytest.mark.parametrize("sigla", CAMPI_ESPERADOS)
    def test_cada_campus_oferta_as_cinco_disciplinas(self, sigla):
        assert [d.rotulo for d in listar_disciplinas(sigla)] == DISCIPLINAS_ESPERADAS

    def test_o_catalogo_cobre_exatamente_os_campi_cadastrados(self):
        siglas_cadastradas = {campus.sigla for campus in CAMPI.values()}
        assert set(CODIGOS_POR_TURMA) == siglas_cadastradas

    @pytest.mark.parametrize("sigla", CAMPI_ESPERADOS)
    @pytest.mark.parametrize("rotulo", DISCIPLINAS_ESPERADAS)
    def test_disciplinas_ainda_sem_codigos_cadastrados(self, sigla, rotulo):
        assert listar_codigos(sigla, Disciplina[rotulo]) == []

    def test_os_campi_nao_partilham_o_mesmo_dicionario(self):
        # Cadastrar um código num campus não pode aparecer no outro.
        assert CODIGOS_POR_TURMA["pbe"] is not CODIGOS_POR_TURMA["pco"]

    def test_nao_ha_selecao_de_turno(self):
        # O curso é ofertado apenas à noite, por isso o catálogo lista os códigos
        # diretamente sob a disciplina, sem nível de turno.
        import app.models.turma as turma

        assert not hasattr(turma, "Turno")
        assert not hasattr(turma, "listar_turnos")

    def test_nao_ha_codigo_repetido_dentro_do_campus(self):
        for sigla, disciplinas in CODIGOS_POR_TURMA.items():
            codigos = [c for cs in disciplinas.values() for c in cs]
            assert len(codigos) == len(set(codigos)), f"código repetido em {sigla}"

    def test_todos_os_codigos_sao_numericos(self):
        from app.utils import github_utils

        for disciplinas in CODIGOS_POR_TURMA.values():
            for codigos in disciplinas.values():
                for codigo in codigos:
                    assert github_utils.validar_codigo_disciplina(codigo)


class TestConsultasSemCadastro:

    def test_campus_desconhecido_nao_quebra(self):
        assert listar_disciplinas("xxx") == []
        assert listar_codigos("xxx", Disciplina.TIAW) == []


class TestValidacaoDeCodigo:

    def test_codigo_inventado_nao_vale(self):
        assert codigo_valido("pco", "0000000") is False

    def test_sem_catalogo_nenhum_codigo_vale(self):
        # Com o catálogo por preencher, nada é aceito — o que impede a criação de
        # repositórios com código errado enquanto os códigos de ADS não chegam.
        assert codigo_valido("pco", "7116101") is False
        assert codigo_valido("pbe", "7116101") is False


class TestChaveDeVerificacaoDoLote:
    """
    A verificação prévia é reaproveitada enquanto a chave não muda. Se a turma ficasse
    de fora dela, trocar a disciplina reaproveitaria nomes de repositório antigos.
    """

    @staticmethod
    def chave(organizacao="org", disciplina=Disciplina.TIAW, codigo="0427100", conteudo="Repositorio: X"):
        from app.views.criacao_lote_view import chave_de_verificacao
        return chave_de_verificacao(organizacao, disciplina, codigo, conteudo)

    def test_mesmos_dados_geram_a_mesma_chave(self):
        assert self.chave() == self.chave()

    def test_trocar_a_disciplina_muda_a_chave(self):
        assert self.chave(disciplina=Disciplina.TIAI) != self.chave()

    def test_trocar_o_codigo_da_turma_muda_a_chave(self):
        assert self.chave(codigo="9623100") != self.chave()

    def test_trocar_a_organizacao_muda_a_chave(self):
        assert self.chave(organizacao="outra") != self.chave()

    def test_trocar_o_arquivo_muda_a_chave(self):
        assert self.chave(conteudo="Repositorio: Y") != self.chave()
