# Radar de Carreira IA

Um projeto de **ciência de dados e machine learning em Python** que transforma vagas públicas em um mapa de competências e em um plano de aprendizado explicável.

O diferencial é o **simulador “E se eu aprender…”**: informe suas competências, adicione uma habilidade e veja como a cobertura muda sobre a mesma amostra de vagas. Todos os cálculos, a preparação dos dados e os modelos são executados em Python. HTML, CSS e JavaScript compõem a interface do navegador.

## Abrir o projeto

No Windows, extraia o ZIP e dê dois cliques em **INICIAR.bat**. O inicializador cria um ambiente virtual, instala as dependências e abre o aplicativo no navegador. A primeira execução requer internet para instalar bibliotecas. Depois, a análise funciona com os dados locais, sem chave de API nem serviço de IA pago.

Requisito: **Python 3.12 ou superior**. Validado com Python 3.12.14. O inicializador também reconhece o Python que acompanha o Codex neste computador. Mantenha a janela do servidor aberta enquanto usa o aplicativo; feche-a ou pressione Ctrl+C para encerrar.

Em qualquer sistema:

```bash
python iniciar.py
```

Para desenvolvimento, sem o inicializador:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python app.py --open
# Linux/macOS:
# .venv/bin/python -m pip install -r requirements-dev.txt
# .venv/bin/python app.py --open
```

O servidor escuta apenas neste computador, na porta 8765. Se ela estiver ocupada, execute `python app.py --port 8766 --open`. O projeto entregue é local; não depende de hospedagem pública.

## O que experimentar

1. **Visão geral:** filtre área, localidade e cargo; confira as competências mais mencionadas. Clique nas barras para filtrar e na legenda do mapa para destacar um grupo.
2. **Meu radar:** edite o perfil de exemplo e clique em Encontrar conexões. As vagas mostram o que combina e o que ainda falta.
3. **Simulação:** adicione AWS, Docker ou outra competência. Compare cobertura atual e simulada sem mudar a população de referência.
4. **Plano de exploração:** veja sugestões de prática ordenadas pelo ganho de cobertura. Exporte o resultado em JSON.
5. **Laboratório ML:** inspecione clustering, baseline, classificação, matriz de confusão e separação de empresas entre treino e teste.
6. **Sobre os dados:** confira a coleta, a atribuição, os limites da amostra e o hash de integridade.

## Dados reais e escopo

A base entregue contém **316 anúncios únicos**, provenientes de 317 registros da API pública do Jobicy; uma duplicata foi removida. Coleta em 19/09/2026 no horário de Brasília (20/09/2026 em UTC). São duas categorias: Data Science & Analytics e Software Engineering, com até 200 anúncios por consulta. Os anúncios, as empresas e as descrições são reais; não há vagas sintéticas misturadas à base. Perfis de demonstração são exemplos editáveis.

Essa é uma amostra de conveniência de vagas remotas internacionais, majoritariamente em inglês. **Não representa o mercado brasileiro ou todo o mercado de trabalho.** Frequência de menções não significa crescimento temporal. Remoto não significa elegibilidade em qualquer país. Anúncios podem expirar após a coleta.

Origem, condições de uso e atribuição: [DATA_SOURCE.md](DATA_SOURCE.md).

## Ciência de dados e ML

| Etapa | Implementação | Como interpretar |
|---|---|---|
| Coleta e preparação | urllib, HTMLParser, deduplicação por ID e conteúdo, validação de URL | Remove HTML ativo e preserva a origem |
| Extração de competências | Dicionário auditável com aliases PT/EN e limites de palavra | Regras, não um modelo de linguagem |
| Análise exploratória | pandas, contagens e proporções | Descreve a amostra filtrada |
| Recomendação | TF-IDF, cosseno e cobertura com pesos IDF | Afinidade explicável, não probabilidade |
| Agrupamento | K-means, k de 2 a 6, silhouette cosseno | Grupos exploratórios de competências |
| Mapa de vagas | TruncatedSVD em duas dimensões | Projeção aproximada com perda de informação |
| Experimento supervisionado | TF-IDF + regressão logística | Prediz as categorias atribuídas pela fonte |
| Avaliação | Split por empresa, baseline, macro-F1, acurácia e matriz de confusão | Experimento separado do ranking |

**Afinidade = 100 × (0,65 × cobertura ponderada + 0,35 × similaridade textual).**

Na cobertura, cada competência tem peso `log((1 + N) / (1 + frequência)) + 1`. O numerador soma os pesos das competências da vaga que aparecem no perfil; o denominador soma os pesos de todas as competências extraídas daquela vaga. Uma vaga sem competências reconhecidas recebe cobertura zero.

A simulação mantém a similaridade textual fixa e altera apenas as competências consideradas presentes. A média usa o mesmo conjunto de vagas filtradas com competências reconhecidas. Assim, o ganho exibido tem uma definição verificável. O plano ordena cada competência ausente pelo ganho médio marginal. Não considera horas de estudo, dificuldade, domínio real ou retorno financeiro.

Os pesos de afinidade são uma escolha do protótipo, sem calibração em resultados de contratação. O extrator não compreende negação nem distingue requisitos de diferenciais; informe apenas competências que você realmente possui. Não há avaliação humana de relevância do ranking.

## Reproduzir a avaliação

```bash
python train.py
python -m pytest -q
```

O script gera `reports/model_report.json` com versões das bibliotecas, hash dos dados, resultados e semente 42. O classificador usa `GroupShuffleSplit`: 25% das empresas no teste. O TF-IDF desse experimento é ajustado somente no treino, e o teste não é usado para escolher hiperparâmetros. Os modelos exploratórios do dashboard usam toda a amostra; são independentes do experimento supervisionado.

As métricas do classificador **não validam o ranking de vagas**. O silhouette é calculado na mesma amostra usada para escolher k; é um diagnóstico interno, não uma estimativa de desempenho futuro. Veja também [RELATORIO.md](RELATORIO.md) e o notebook `notebooks/01_exploracao_e_modelagem.ipynb`.

## Atualizar os dados

```bash
python collect.py
python train.py
```

Reinicie o aplicativo após a atualização. A coleta é manual e exige um intervalo de seis horas entre atualizações; não há agendamento. Falhas de rede, respostas inválidas ou vazias preservam o último arquivo válido. A interface não apresenta métricas de uma versão antiga da base.

## Organização

```text
app.py                  Servidor Flask e API
iniciar.py / INICIAR.bat Inicialização local
collect.py              Atualização manual da amostra
train.py                Avaliação reproduzível
radar/data.py           Coleta, limpeza e rastreabilidade
radar/skills.py         Vocabulário e sugestões de prática
radar/model.py          Recomendação, K-means e SVD
radar/analytics.py      Filtros e estatísticas
radar/evaluation.py     Experimento supervisionado
data/jobs.json          Base real tratada e metadados
reports/               Métricas e versões
notebooks/             Análise didática reproduzível
templates/ + static/   Interface sem dependências externas
tests/                 Testes do pipeline e da API
```

O perfil não é gravado em arquivos ou banco de dados, nem enviado a fornecedores de IA. Exportações contêm competências reconhecidas e resultados, sem o texto completo digitado. O aplicativo vincula anúncios à fonte original e trata descrições como texto. A licença MIT cobre apenas o código original, não os anúncios.
