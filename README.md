# Radar de Carreira IA

**Ciência de dados para explorar oportunidades e planejar o próximo passo no aprendizado.**

O Radar de Carreira IA é uma aplicação em **Python** que analisa vagas reais, identifica competências e mostra conexões entre o que você já sabe e o que aparece nos anúncios. A proposta é transformar descrições de vagas em informações que ajudem a organizar os estudos, com resultados que podem ser entendidos e conferidos.

**[Acesse o projeto no Render e experimente](https://radar-carreira-ia.onrender.com/)**

Não precisa instalar nada nem criar uma conta. Abra o aplicativo, escolha um perfil de exemplo e explore. Como a hospedagem usa uma instância gratuita, o primeiro acesso após um período de inatividade pode levar cerca de um minuto ou mais.

## A ideia por trás do projeto

Com tantas ferramentas, linguagens e assuntos para estudar, escolher por onde começar nem sempre é simples. O Radar parte de uma pergunta prática: **quais competências se conectam ao meu repertório e às vagas desta amostra?**

O diferencial está no simulador **“E se eu aprender…”**. Você adiciona uma competência, como AWS ou Docker, e compara a cobertura antes e depois, mantendo o mesmo conjunto de vagas. É uma forma de explorar possibilidades com dados e entender o motivo de cada resultado.

O projeto foi desenvolvido como uma aplicação de portfólio, reunindo coleta, tratamento de dados, análise exploratória, machine learning, avaliação e publicação de uma aplicação web.

## O que você pode fazer

| Recurso | Como funciona |
|---|---|
| **Visão geral** | Explore a amostra por área, localidade, cargo, empresa ou competência e veja os indicadores atualizados. |
| **Mapa de oportunidades** | Visualize grupos de vagas com competências semelhantes, organizados com K-means. |
| **Meu radar** | Informe suas competências e receba uma lista de vagas ordenada por afinidade, com o que combina e o que falta. |
| **Simulador de aprendizado** | Adicione competências e observe como a cobertura das vagas muda. |
| **Plano de exploração** | Consulte sugestões de prática ordenadas pelo ganho de cobertura e exporte o resultado em JSON. |
| **Laboratório ML** | Confira os métodos, as métricas, o baseline e os limites dos modelos. |
| **Sobre os dados** | Veja a origem da base, a data de coleta e os cuidados necessários ao interpretar os resultados. |

## Um jeito rápido de testar

1. Acesse a [demonstração online](https://radar-carreira-ia.onrender.com/).
2. Entre em **Meu radar** e use o perfil de exemplo **Dados**, ou escreva suas próprias competências.
3. Clique em **Encontrar conexões** para explorar as recomendações.
4. Em **E se eu aprender…**, adicione **AWS** e compare os resultados.
5. Abra as explicações das vagas e, se quiser, clique em **Exportar plano**.

Na base incluída, o perfil de exemplo de dados passa de **18,0% para 21,4% de cobertura média** ao adicionar AWS, considerando as mesmas 286 vagas com competências reconhecidas. Esse número descreve a cobertura da amostra; não representa chance de contratação.

## Os dados utilizados

A versão inicial reúne **316 anúncios únicos de 158 empresas**, obtidos pela API pública do **Jobicy**, nas categorias Data Science & Analytics e Software Engineering. A coleta ocorreu em **19/09/2026, no horário de Brasília** — 20/09/2026 em UTC. Dos 317 registros recebidos, uma duplicata foi removida.

O vocabulário do projeto reconhece **53 competências**, com termos e variações em português e inglês. Os anúncios são reais; os perfis de demonstração são exemplos editáveis. A base é uma fotografia daquela coleta, com atualização manual.

Trata-se de uma amostra de vagas remotas internacionais, majoritariamente em inglês. Ela não representa todo o mercado de trabalho nem especificamente o mercado brasileiro. Os anúncios podem expirar, e uma vaga remota pode restringir o país de contratação. Cada recomendação mantém o link para a publicação original.

Consulte a [documentação da fonte e das condições de uso](DATA_SOURCE.md).

## Como a ciência de dados entra aqui

O processamento e os modelos são executados em Python. Flask e Waitress servem a aplicação; pandas e NumPy apoiam a análise; scikit-learn implementa os modelos. A interface utiliza HTML, CSS e JavaScript.

| Etapa | Técnica utilizada |
|---|---|
| Coleta e preparação | Consulta à API, limpeza de HTML, deduplicação e validação dos links de origem. |
| Extração de competências | Dicionário auditável de termos e aliases, com regras de identificação. |
| Análise exploratória | Contagens, proporções e filtros com pandas. |
| Recomendação | TF-IDF, similaridade do cosseno e cobertura de competências ponderada por IDF. |
| Agrupamento de vagas | K-means, comparando de 2 a 6 grupos pelo silhouette cosseno. |
| Visualização dos grupos | TruncatedSVD para projetar as vagas em duas dimensões. |
| Experimento supervisionado | TF-IDF + regressão logística para distinguir as categorias da fonte. |

A afinidade combina **65% de cobertura ponderada de competências** e **35% de similaridade textual**. Esses pesos são uma escolha do protótipo, sem calibração com resultados reais de contratação. A simulação mantém a similaridade textual fixa e altera apenas as competências consideradas presentes.

O plano sugere as competências ausentes com maior ganho médio de cobertura no recorte selecionado. Ele não estima tempo de estudo, dificuldade, proficiência ou retorno financeiro.

### Avaliação dos modelos

No experimento de classificação, as empresas foram separadas entre treino e teste: **223 vagas no treino e 93 no teste**, sem empresas compartilhadas. O vocabulário TF-IDF foi ajustado somente no treino.

| Métrica | Regressão logística | Baseline da classe mais frequente |
|---|---:|---:|
| Macro-F1 | 0,881 | 0,422 |
| Acurácia | 90,3% | 73,1% |

Esses resultados medem a capacidade de reproduzir as categorias atribuídas pelo Jobicy em um único recorte de teste. **Eles não avaliam a qualidade do ranking de vagas.**

No agrupamento, foram selecionados 6 grupos, com silhouette de **0,1585**, indicando sobreposição entre os grupos. A projeção em duas dimensões preserva **12,7% da variância**, por isso as distâncias no mapa são aproximadas. O silhouette é um diagnóstico interno da amostra usada para escolher o número de grupos.

Para explorar os detalhes, consulte o [relatório técnico](RELATORIO.md), o [notebook de análise e modelagem](notebooks/01_exploracao_e_modelagem.ipynb) e o [relatório de métricas em JSON](reports/model_report.json).

## Executar localmente

O ambiente foi validado com **Python 3.12.14**. A primeira instalação requer internet; depois, o aplicativo utiliza a base incluída no repositório, sem chave de API ou serviço de IA pago.

```bash
git clone https://github.com/arthurbueno150-create/radar-carreira-ia.git
cd radar-carreira-ia
python iniciar.py
```

O inicializador cria um ambiente virtual, instala as dependências e abre o aplicativo no navegador. No Windows, também é possível usar **INICIAR.bat**. Mantenha a janela do servidor aberta enquanto utiliza a aplicação.

Para preparar um ambiente de desenvolvimento manualmente:

```bash
python -m venv .venv
```

No Windows:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python app.py --open
```

No Linux ou macOS:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python app.py --open
```

A execução local usa a porta 8765. Caso esteja ocupada, adicione `--port 8766` ao comando de inicialização.

## Reproduzir a análise e os testes

Com as dependências de desenvolvimento instaladas, execute no ambiente virtual:

```bash
python train.py
python -m pytest -q
```

A avaliação usa a semente 42 e registra versões das bibliotecas e o hash da base em `reports/model_report.json`. Os testes cobrem preparação dos dados, filtros, recomendações, simulação, exportação, validação das entradas e consistência da avaliação.

Para renovar a amostra:

```bash
python collect.py
python train.py
```

A coleta é manual, respeita um intervalo mínimo de seis horas e preserva a última base válida em caso de falha. Reinicie a aplicação após atualizar os dados. Para atualizar a versão online, envie a base e o relatório gerados ao repositório. Métricas de uma base anterior deixam de aparecer até que a avaliação seja refeita.

## Publicação no Render

O arquivo [render.yaml](render.yaml) descreve o serviço web: Python 3.12.14, instalação por `pip install -r requirements.txt`, inicialização por `python app.py` e verificação de saúde em `/health`.

O servidor utiliza a porta fornecida pelo Render e `RADAR_HOST=0.0.0.0` para receber acessos públicos. Os modelos exploratórios são preparados na inicialização. A versão publicada está conectada à branch `main`, com implantação automática após novos commits.

## Estrutura do repositório

```text
app.py                  Servidor Flask e API
iniciar.py / INICIAR.bat Inicialização local
collect.py              Atualização manual dos dados
train.py                Avaliação reproduzível
radar/                  Preparação, análise, competências e modelos
data/                   Amostra de vagas e metadados de origem
reports/                Métricas e versões das bibliotecas
notebooks/              Análise exploratória e modelagem
templates/ + static/    Interface do aplicativo
tests/                  Testes do pipeline e da API
render.yaml             Configuração de publicação
```

## Privacidade e limites

O perfil é enviado ao servidor do aplicativo apenas para calcular os resultados. O código não grava esse texto em arquivos, banco de dados ou logs e não utiliza APIs de IA externas. A exportação contém competências reconhecidas, resultados e origem dos dados, sem incluir o texto completo digitado. Uma lista de competências é suficiente para testar.

O reconhecimento de competências usa regras: não compreende negações nem distingue requisitos de diferenciais. Por isso, informe apenas o que você sabe. A frequência de uma competência nesta coleta também não demonstra crescimento da demanda ao longo do tempo. Não há avaliação humana de relevância do ranking.

## Licença e colaboração

O código original está disponível sob a [licença MIT](LICENSE). Os anúncios pertencem aos seus respectivos titulares e seguem as condições da fonte; a licença do código não transfere direitos sobre esses conteúdos.

Encontrou algo que pode melhorar? Issues e pull requests são bem-vindos. Sugestões para o vocabulário, a experiência de uso e a avaliação dos modelos são ótimos pontos de partida.
