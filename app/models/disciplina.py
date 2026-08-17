from enum import Enum
from typing import List


class Disciplina(Enum):
    """
    Enumeração das disciplinas de Trabalho Interdisciplinar de Análise e
    Desenvolvimento de Sistemas.

    Cada disciplina é ofertada num período fixo do curso, de modo que a escolha da
    disciplina já determina o período: o professor não informa os dois.

    O valor de cada membro é a sigla usada no nome padronizado do repositório
    (ex: 'tidai' em '2026-1-p3-tidai-adota-pet'), e os membros estão na ordem dos períodos.

    | Sigla | Período | Disciplina                              |
    |-------|---------|-----------------------------------------|
    | TIAW  | p1      | Aplicações Web                          |
    | TIAPN | p2      | Aplicações para Processos de Negócios   |
    | TIDAI | p3      | Desenvolvimento de Aplicação Interativa |
    | TIAM  | p4      | Aplicação Móvel                         |
    | TIAI  | p5      | Aplicações Inovadoras                   |
    """
    TIAW = ("tiaw", 1)
    TIAPN = ("tiapn", 2)
    TIDAI = ("tidai", 3)
    TIAM = ("tiam", 4)
    TIAI = ("tiai", 5)

    def __new__(cls, sigla: str, periodo: int):
        # O valor do membro continua sendo apenas a sigla, que é o que entra no nome do
        # repositório; o período fica como atributo, ao lado dela e não num mapa à parte.
        membro = object.__new__(cls)
        membro._value_ = sigla
        membro.periodo = periodo
        return membro

    @property
    def sigla(self) -> str:
        """Retorna a sigla usada no nome do repositório (ex: tidai)."""
        return self.value

    @property
    def rotulo_periodo(self) -> str:
        """Retorna o período no formato usado no nome do repositório (ex: p3)."""
        return f"p{self.periodo}"

    @property
    def rotulo(self) -> str:
        """Retorna o rótulo da disciplina para exibição na interface (ex: TIAW)."""
        return self.name

    @classmethod
    def listar_rotulos(cls) -> List[str]:
        """
        Retorna os rótulos de todas as disciplinas, na ordem dos períodos.

        Returns:
            List[str]: Rótulos das disciplinas disponíveis para seleção.
        """
        return [disciplina.rotulo for disciplina in cls]

    def __str__(self) -> str:
        return self.rotulo
