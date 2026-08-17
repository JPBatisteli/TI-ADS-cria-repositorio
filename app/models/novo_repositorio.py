from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.models.aluno import Aluno
from app.models.campus import Campus
from app.models.disciplina import Disciplina
from app.models.periodo_letivo import PeriodoLetivo
from app.models.template import Template, obter_template
from app.utils import github_utils


@dataclass
class NovoRepositorio:
    """
    Representa a solicitação de criação de um repositório de Trabalho Interdisciplinar.

    O objeto reúne os dados informados pelo professor, monta o nome padronizado
    do repositório e valida esses dados antes que a criação seja enviada ao GitHub.

    O padrão de nomenclatura adotado é:
        <ano>-<semestre>-<periodo>-<sigla_disciplina>-<nome_projeto>

    Exemplo:
        2026-1-p3-tidai-adota-pet

    O período vem da disciplina escolhida, e o campus não aparece no nome — ele decide
    apenas em que organização do GitHub o repositório é criado.

    Attributes:
        campus (Campus): Campus em que a disciplina é lecionada.
        disciplina (Disciplina): Disciplina de TI (TIAW, TIAPN, TIDAI, TIAM ou TIAI).
        codigo_disciplina (str): Código numérico da turma (ex: 2401100). Não entra no
                                 nome do repositório: é registado apenas como
                                 identificação da turma, e pode ficar vazio.
        nome_projeto (str): Nome do projeto/equipe informado pelo professor.
        ano (int): Ano letivo.
        semestre (int): Semestre letivo (1 ou 2).
        descricao (str): Descrição opcional do repositório.
        privado (bool): Indica se o repositório deve ser criado como privado. Os
                        repositórios de TI são sempre privados, por decisão institucional.
        alunos (List[Aluno]): Alunos a serem adicionados como colaboradores.
        criar_equipe (bool): Indica se deve ser criada uma equipe para o repositório.
        nome_equipe_personalizado (str): Nome informado pelo professor para a equipe.
                                         Quando vazio, o nome é derivado do repositório.
        periodo_letivo_atual (PeriodoLetivo): Período letivo em andamento, contra o qual
                                              o ano e o semestre informados são validados.
        erros (List[str]): Erros encontrados durante a validação dos dados.
    """
    campus: Campus
    disciplina: Disciplina
    nome_projeto: str
    codigo_disciplina: str = ""
    ano: int = field(default_factory=lambda: PeriodoLetivo.atual().ano)
    semestre: int = field(default_factory=lambda: PeriodoLetivo.atual().semestre)
    descricao: str = ""
    privado: bool = True
    alunos: List[Aluno] = field(default_factory=list)
    criar_equipe: bool = False
    nome_equipe_personalizado: str = ""
    periodo_letivo_atual: PeriodoLetivo = field(default_factory=PeriodoLetivo.atual)
    erros: List[str] = field(default_factory=list)

    @property
    def nome_equipe_derivado(self) -> str:
        """
        Retorna o nome de equipe gerado automaticamente.

        Corresponde ao nome do repositório, que já é único na organização por seguir
        o padrão de nomenclatura adotado.

        Returns:
            str: Nome da equipe sugerido pela aplicação.
        """
        return self.nome

    @property
    def equipe_com_nome_personalizado(self) -> bool:
        """Indica se o professor informou um nome próprio para a equipe."""
        return bool(self.nome_equipe_personalizado.strip())

    @property
    def nome_equipe(self) -> str:
        """
        Retorna o nome da equipe a ser criada.

        Usa o nome informado pelo professor quando houver; caso contrário, o nome
        derivado do repositório.

        Returns:
            str: Nome da equipe a ser criada.
        """
        if self.equipe_com_nome_personalizado:
            return self.nome_equipe_personalizado.strip()
        return self.nome_equipe_derivado

    @property
    def alunos_unicos(self) -> List[Aluno]:
        """
        Retorna os alunos sem repetições, preservando a ordem de inclusão.

        A comparação ignora maiúsculas e minúsculas, já que os nomes de usuário do
        GitHub não as diferenciam.

        Returns:
            List[Aluno]: Alunos distintos informados pelo professor.
        """
        vistos = set()
        alunos = []

        for aluno in self.alunos:
            if aluno.username_normalizado not in vistos:
                vistos.add(aluno.username_normalizado)
                alunos.append(aluno)

        return alunos

    @property
    def prefixo(self) -> str:
        """
        Retorna o prefixo do repositório, comum a toda a turma.

        O campus não entra no nome: os repositórios de cada campus já ficam separados
        pela organização do GitHub em que são criados.

        Returns:
            str: Prefixo no formato <ano>-<semestre>-<periodo>-<sigla_disciplina>.
        """
        return (
            f"{self.ano}-{self.semestre}-"
            f"{self.disciplina.rotulo_periodo}-{self.disciplina.sigla}"
        )

    @property
    def nome(self) -> str:
        """
        Retorna o nome completo do repositório, já no padrão institucional.

        Returns:
            str: Nome padronizado do repositório.
        """
        return f"{self.prefixo}-{github_utils.gerar_slug(self.nome_projeto)}"

    @property
    def url(self) -> str:
        """Retorna a URL que o repositório terá dentro da organização do campus."""
        return f"{self.campus.url_organizacao}/{self.nome}"

    @property
    def template(self) -> Optional[Template]:
        """
        Retorna o repositório-modelo da disciplina no campus, quando houver.

        Cada disciplina de ADS tem o seu modelo, na organização do próprio campus.

        Returns:
            Optional[Template]: Modelo a ser usado como base do repositório, ou None
                                quando a disciplina não tiver modelo cadastrado.
        """
        return obter_template(self.campus.sigla, self.campus.organizacao, self.disciplina)

    @property
    def usa_template(self) -> bool:
        """Indica que o repositório será gerado a partir de um repositório-modelo."""
        return self.template is not None

    def _validar_codigo_disciplina(self):
        """
        Valida o código da turma, quando informado.

        O código deixou de compor o nome do repositório, por isso não é obrigatório:
        serve apenas para identificar a turma nos relatórios. Continua sendo validado
        quando preenchido, para que um código malformado não chegue ao `.csv`.
        """
        codigo = self.codigo_disciplina.strip()

        if codigo and not github_utils.validar_codigo_disciplina(codigo):
            self.erros.append("O código da turma deve conter apenas dígitos (ex: 2401100).")

    def _validar_nome_projeto(self):
        """Valida se o nome do projeto foi preenchido e gera um slug utilizável."""
        if not self.nome_projeto.strip():
            self.erros.append("Informe o nome do repositório.")
        elif not github_utils.gerar_slug(self.nome_projeto):
            self.erros.append(
                "O nome do repositório deve conter ao menos uma letra ou dígito "
                "(ex: 'Brechó Re-Use')."
            )

    def _validar_periodo_letivo(self):
        """
        Valida se o ano e o semestre correspondem ao período letivo em andamento.

        O período é determinado pela data corrente, e não escolhido livremente, para
        impedir a criação de repositórios em semestres já encerrados ou futuros.
        """
        if PeriodoLetivo(ano=self.ano, semestre=self.semestre) != self.periodo_letivo_atual:
            self.erros.append(
                f"O período letivo deve ser o atual ({self.periodo_letivo_atual})."
            )

    def _validar_nome_repositorio(self):
        """
        Valida o nome final do repositório contra o padrão institucional e contra
        o limite de caracteres aceito pelo GitHub.
        """
        nome = self.nome

        if len(nome) > github_utils.TAMANHO_MAXIMO_NOME_REPOSITORIO:
            self.erros.append(
                f"O nome gerado possui {len(nome)} caracteres e excede o limite de "
                f"{github_utils.TAMANHO_MAXIMO_NOME_REPOSITORIO} caracteres do GitHub. "
                "Use um nome de projeto mais curto."
            )
        elif not github_utils.validar_nome_repositorio(nome):
            self.erros.append(f"O nome gerado ('{nome}') não segue o padrão de nomenclatura adotado.")

    def validar(self) -> bool:
        """
        Executa a validação de todos os dados informados.

        A lista de erros é reiniciada a cada chamada, de modo que o objeto possa
        ser revalidado após correções feitas pelo professor.

        Returns:
            bool: True se não houver erros, False caso contrário.
        """
        self.erros = []

        self._validar_codigo_disciplina()
        self._validar_nome_projeto()
        self._validar_periodo_letivo()

        # O nome final só faz sentido se os componentes que o formam forem válidos.
        if not self.erros:
            self._validar_nome_repositorio()

        return len(self.erros) == 0

    def __str__(self) -> str:
        """Retorna uma representação legível da solicitação de criação."""
        return f"{self.nome} ({self.campus.organizacao})"

    def to_dict(self) -> dict:
        """
        Converte o objeto num dicionário, útil para exibição em tabelas e logs.

        Returns:
            dict: Dicionário com os dados da solicitação e o nome gerado.
        """
        return {
            "campus": self.campus.nome,
            "organizacao": self.campus.organizacao,
            "disciplina": self.disciplina.rotulo,
            "codigo_disciplina": self.codigo_disciplina.strip(),
            "ano": self.ano,
            "semestre": self.semestre,
            "nome": self.nome,
            "url": self.url,
            "privado": self.privado,
        }
