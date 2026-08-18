import pytest
import requests

from app.controllers.criacao_repositorio_controller import CriacaoRepositorioController
from app.models.arquivo_lote import ArquivoLote
from app.models.campus import Campus, obter_campus
from app.models.disciplina import Disciplina
from app.models.novo_repositorio import NovoRepositorio
from app.models.template import MODELOS_POR_CAMPUS, Template, obter_template
from app.services.github_service import GithubService, GithubServiceError

from test_criacao_de_equipe import GithubServiceFalso, criar_controller
from test_github_service import RespostaFalsa

ORG_CONTAGEM = "ICEI-PUC-Minas-PCO-ADS-TI"
ORG_BETIM = "ICEI-PUC-Minas-PBE-ADS-TI"

# Campus fictício, usado nos casos em que o que está sob teste é a ausência de modelo.
CAMPUS_SEM_MODELO = Campus(sigla="xxx", nome="Sem Modelo", organizacao="Org")

# Espelho do cadastro de modelos, escrito de forma independente para que uma alteração
# acidental nele seja detectada. Os dois campi usam os mesmos nomes de modelo.
MODELOS_ESPERADOS = {
    Disciplina.TIAW: "Template-TIAWFE",
    Disciplina.TIAPN: "Template-TIAPN",
    Disciplina.TIDAI: "Template-TIDAI",
    Disciplina.TIAM: "Template-TIAM",
    Disciplina.TIAI: "Template-TIAI",
}


def solicitacao_em(disciplina=Disciplina.TIAW, campus="Contagem", **extras) -> NovoRepositorio:
    return NovoRepositorio(
        campus=campus if isinstance(campus, Campus) else obter_campus(campus),
        disciplina=disciplina,
        codigo_disciplina="2401100",
        nome_projeto="Adota Pet",
        **extras
    )


class TestModeloPorDisciplina:

    @pytest.mark.parametrize("disciplina, repositorio", MODELOS_ESPERADOS.items())
    def test_cada_disciplina_tem_o_seu_modelo(self, disciplina, repositorio):
        template = obter_template("pco", ORG_CONTAGEM, disciplina)

        assert template == Template(owner=ORG_CONTAGEM, repositorio=repositorio)

    @pytest.mark.parametrize("sigla", ["pbe", "pco"])
    def test_os_dois_campi_tem_modelo_para_todas_as_disciplinas(self, sigla):
        assert set(MODELOS_POR_CAMPUS[sigla]) == set(Disciplina)

    @pytest.mark.parametrize("disciplina, repositorio", MODELOS_ESPERADOS.items())
    def test_betim_usa_os_mesmos_modelos_na_sua_organizacao(self, disciplina, repositorio):
        template = obter_template("pbe", ORG_BETIM, disciplina)

        assert template == Template(owner=ORG_BETIM, repositorio=repositorio)

    def test_o_modelo_fica_na_organizacao_do_campus(self):
        template = obter_template("pco", ORG_CONTAGEM, Disciplina.TIAM)

        assert template.owner == ORG_CONTAGEM
        assert template.nome_completo == f"{ORG_CONTAGEM}/Template-TIAM"
        assert template.url == f"https://github.com/{ORG_CONTAGEM}/Template-TIAM"

    def test_tiaw_usa_o_modelo_tiawfe(self):
        # TIAW é a abreviação de TIAWFE; a sigla do modelo é a forma extensa da mesma
        # disciplina, e não a de uma disciplina diferente.
        assert obter_template("pco", ORG_CONTAGEM, Disciplina.TIAW).repositorio == "Template-TIAWFE"

    def test_campus_sem_modelos_cadastrados(self):
        assert obter_template(CAMPUS_SEM_MODELO.sigla, "Org", Disciplina.TIAW) is None


class TestTemplateDaSolicitacao:

    @pytest.mark.parametrize("disciplina, repositorio", MODELOS_ESPERADOS.items())
    def test_solicitacao_adota_o_modelo_da_sua_disciplina(self, disciplina, repositorio):
        solicitacao = solicitacao_em(disciplina)

        assert solicitacao.usa_template is True
        assert solicitacao.template.owner == ORG_CONTAGEM
        assert solicitacao.template.repositorio == repositorio

    def test_trocar_a_disciplina_troca_o_modelo(self):
        assert solicitacao_em(Disciplina.TIAM).template != solicitacao_em(Disciplina.TIAI).template

    def test_campus_sem_modelo_nao_usa_template(self):
        solicitacao = solicitacao_em(campus=CAMPUS_SEM_MODELO)

        assert solicitacao.usa_template is False
        assert solicitacao.template is None

    def test_betim_adota_o_modelo_da_propria_organizacao(self):
        solicitacao = solicitacao_em(Disciplina.TIDAI, campus="Betim")

        assert solicitacao.template == Template(owner=ORG_BETIM, repositorio="Template-TIDAI")


class TestCriacaoAPartirDoModelo:

    def test_usa_o_modelo_da_disciplina_selecionada(self):
        service = GithubServiceFalso()
        criar_controller(service).criar_repositorio(
            solicitacao_em(Disciplina.TIDAI, criar_equipe=False)
        )

        assert service.templates_usados == [f"{ORG_CONTAGEM}/Template-TIDAI"]

    def test_cada_disciplina_usa_o_proprio_modelo(self):
        service = GithubServiceFalso()
        controller = criar_controller(service)

        controller.criar_repositorio(solicitacao_em(Disciplina.TIAPN, criar_equipe=False))
        controller.criar_repositorio(solicitacao_em(Disciplina.TIAI, criar_equipe=False))

        assert service.templates_usados == [
            f"{ORG_CONTAGEM}/Template-TIAPN",
            f"{ORG_CONTAGEM}/Template-TIAI",
        ]

    def test_repositorio_e_criado_normalmente(self):
        service = GithubServiceFalso()
        resultado = criar_controller(service).criar_repositorio(
            solicitacao_em(criar_equipe=False)
        )

        assert resultado.sucesso is True
        assert resultado.url

    def test_campus_sem_modelo_cria_repositorio_vazio(self):
        service = GithubServiceFalso()
        resultado = criar_controller(service).criar_repositorio(
            solicitacao_em(campus=CAMPUS_SEM_MODELO, criar_equipe=False)
        )

        assert service.templates_usados == []
        assert resultado.sucesso is True


class TestServicoDeGeracaoPorModelo:

    @pytest.fixture
    def service(self) -> GithubService:
        return GithubService(token="token-de-teste")

    def test_envia_os_parametros_esperados(self, service, monkeypatch):
        capturado = {}

        def post_falso(url, headers=None, json=None):
            capturado["url"] = url
            capturado["json"] = json
            return RespostaFalsa(201, {"html_url": "u"})

        monkeypatch.setattr(requests, "post", post_falso)

        service.criar_repositorio_por_template(
            "org-modelo", "Template-TIAW", "org-destino", "repo",
            descricao="TI", privado=True
        )

        assert capturado["url"] == "https://api.github.com/repos/org-modelo/Template-TIAW/generate"
        assert capturado["json"] == {
            "owner": "org-destino",
            "name": "repo",
            "description": "TI",
            "private": True,
            "include_all_branches": False,
        }

    def test_falha_e_propagada(self, service, monkeypatch):
        monkeypatch.setattr(requests, "post", lambda *a, **k: RespostaFalsa(404, {}))

        with pytest.raises(GithubServiceError, match="não encontrado"):
            service.criar_repositorio_por_template("o", "t", "org", "repo")

    def test_repositorio_e_reconhecido_como_modelo(self, service, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: RespostaFalsa(200, {"is_template": True}))
        assert service.e_template("org", "modelo") is True

    def test_repositorio_comum_nao_e_modelo(self, service, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: RespostaFalsa(200, {"is_template": False}))
        assert service.e_template("org", "comum") is False

    def test_repositorio_inexistente_nao_e_modelo(self, service, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: RespostaFalsa(404, {}))
        assert service.e_template("org", "sumido") is False


class TestVerificacaoDoModeloNoLote:

    ARQUIVO = """Repositorio: Projeto A
Grupo: Grupo A
Membros: ana

Repositorio: Projeto B
Grupo: Grupo B
Membros: bruno
"""

    @staticmethod
    def verificar(template_valido: bool, disciplina=Disciplina.TIAW, campus="Contagem"):
        from test_verificacao_lote import GithubServiceFalso as ServiceDeVerificacao

        service = ServiceDeVerificacao(membros=["ana", "bruno"], template_valido=template_valido)
        controller = CriacaoRepositorioController(token="t")
        controller.github_service = service
        solicitacoes = ArquivoLote.de_texto(TestVerificacaoDoModeloNoLote.ARQUIVO).montar_solicitacoes(
            campus if isinstance(campus, Campus) else obter_campus(campus), disciplina, "2401100"
        )
        return controller.verificar_lote(solicitacoes), service

    def test_modelo_valido_libera_a_criacao(self):
        verificacao, _ = self.verificar(template_valido=True)

        assert verificacao.erro_template == ""
        assert verificacao.pode_criar is True

    def test_modelo_invalido_bloqueia_todo_o_lote(self):
        verificacao, _ = self.verificar(template_valido=False)

        assert "não está marcado como template" in verificacao.erro_template
        assert verificacao.pode_criar is False

    def test_o_modelo_e_consultado_uma_unica_vez_por_lote(self):
        _, service = self.verificar(template_valido=True, disciplina=Disciplina.TIAM)

        assert service.consultas_de_template == [f"{ORG_CONTAGEM}/Template-TIAM"]

    def test_campus_sem_modelo_nao_consulta_nada(self):
        verificacao, service = self.verificar(template_valido=False, campus=CAMPUS_SEM_MODELO)

        assert service.consultas_de_template == []
        assert verificacao.erro_template == ""


class TestPadraoFixoDeCriacao:
    """Visibilidade e origem do conteúdo deixaram de ser escolha do professor."""

    def test_repositorio_nasce_privado_sem_precisar_informar(self):
        assert solicitacao_em().privado is True

    def test_a_opcao_de_readme_inicial_deixou_de_existir(self):
        assert not hasattr(solicitacao_em(), "inicializar_readme")

    def test_a_criacao_envia_private_verdadeiro(self):
        capturado = {}

        class ServiceQueCaptura(GithubServiceFalso):
            def criar_repositorio_por_template(self, template_owner, template_repositorio,
                                               nome_organizacao, nome_repositorio, descricao="",
                                               privado=False, incluir_todas_as_branches=False):
                capturado["privado"] = privado
                return super().criar_repositorio_por_template(
                    template_owner, template_repositorio, nome_organizacao,
                    nome_repositorio, descricao, privado, incluir_todas_as_branches
                )

        service = ServiceQueCaptura()
        criar_controller(service).criar_repositorio(solicitacao_em(criar_equipe=False))

        assert capturado["privado"] is True

    def test_a_criacao_sem_modelo_tambem_envia_private_verdadeiro(self):
        capturado = {}

        class ServiceQueCaptura(GithubServiceFalso):
            def criar_repositorio(self, nome_organizacao, nome_repositorio, descricao="",
                                  privado=False, inicializar_readme=True):
                capturado["privado"] = privado
                return super().criar_repositorio(
                    nome_organizacao, nome_repositorio, descricao, privado, inicializar_readme
                )

        service = ServiceQueCaptura()
        criar_controller(service).criar_repositorio(
            solicitacao_em(campus=CAMPUS_SEM_MODELO, criar_equipe=False)
        )

        assert capturado["privado"] is True
