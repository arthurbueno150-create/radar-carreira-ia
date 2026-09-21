"""Vocabulário auditável. A extração de competências é uma regra, não um modelo."""
import re
import unicodedata


def normalize(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(c))


SKILLS = {
    'Python': ['python'], 'SQL': ['sql', 'postgresql', 'mysql', 't-sql', 'tsql'],
    'Pandas': ['pandas'], 'NumPy': ['numpy'], 'Excel': ['excel', 'spreadsheets'],
    'Power BI': ['power bi', 'powerbi'], 'Tableau': ['tableau'],
    'Estatística': ['statistics', 'statistical', 'estatistica', 'estatistico'],
    'Machine Learning': ['machine learning', 'aprendizado de maquina'],
    'Deep Learning': ['deep learning', 'neural networks', 'redes neurais'],
    'Scikit-learn': ['scikit-learn', 'sklearn', 'scikit learn'],
    'PyTorch': ['pytorch'], 'TensorFlow': ['tensorflow'],
    'NLP': ['nlp', 'natural language processing', 'processamento de linguagem natural'],
    'LLMs': ['llm', 'llms', 'large language model', 'large language models', 'modelos de linguagem'],
    'IA generativa': ['generative ai', 'genai', 'gen ai', 'ia generativa'],
    'RAG': ['rag', 'retrieval augmented generation', 'retrieval-augmented generation'],
    'LangChain': ['langchain'], 'MLOps': ['mlops', 'ml ops'],
    'MLflow': ['mlflow'], 'Experimentação': ['a/b testing', 'ab testing', 'a/b tests', 'experimentacao'],
    'Git': ['git', 'github', 'gitlab'], 'Docker': ['docker'],
    'Kubernetes': ['kubernetes', 'k8s'], 'AWS': ['aws', 'amazon web services'],
    'Azure': ['azure'], 'GCP': ['gcp', 'google cloud'],
    'Spark': ['spark', 'pyspark'], 'Airflow': ['airflow'], 'dbt': ['dbt'],
    'Snowflake': ['snowflake'], 'Databricks': ['databricks'], 'BigQuery': ['bigquery'],
    'ETL': ['etl', 'elt', 'data pipelines', 'pipelines de dados'],
    'Kafka': ['kafka'], 'APIs': ['api', 'apis', 'restful', 'fastapi', 'rest api'],
    'JavaScript': ['javascript'], 'TypeScript': ['typescript'], 'React': ['react', 'reactjs'],
    'Node.js': ['node.js', 'nodejs'], 'Java': ['java'], 'Go': ['golang', 'go language'],
    'C++': ['c++'], 'C#': ['c#', 'csharp'], '.NET': ['.net', 'dotnet'],
    'Linux': ['linux'], 'Terraform': ['terraform'], 'CI/CD': ['ci/cd', 'cicd', 'continuous integration'],
    'MongoDB': ['mongodb'], 'Redis': ['redis'], 'Hadoop': ['hadoop'],
    'Visualização': ['data visualization', 'visualizacao de dados', 'dataviz'],
    'Análise de dados': ['data analysis', 'analise de dados', 'data analytics'],
}

PATTERNS = {name: re.compile(r'(?<![a-z0-9])(?:' + '|'.join(
    re.escape(normalize(alias)) for alias in aliases) + r')(?![a-z0-9])')
    for name, aliases in SKILLS.items()}


def extract_skills(text: str) -> list[str]:
    normalized = normalize(text)
    return [name for name, pattern in PATTERNS.items() if pattern.search(normalized)]


def canonical_text(text: str) -> str:
    # Ponte limitada PT/EN; não é tradução ou um modelo multilíngue.
    aliases = [SKILLS[name][0] for name in extract_skills(text)]
    return normalize(text) + ' ' + ' '.join(aliases * 3)


LEARNING = {
    'Python': ('Automatize a limpeza de um conjunto de dados e escreva três testes.', 'https://docs.python.org/pt-br/3/tutorial/'),
    'SQL': ('Modele três tabelas e responda perguntas com JOINs e funções de janela.', 'https://www.postgresql.org/docs/current/tutorial.html'),
    'Pandas': ('Construa uma análise reproduzível com dados ausentes, agrupamentos e junções.', 'https://pandas.pydata.org/docs/getting_started/'),
    'Machine Learning': ('Compare um modelo simples e um baseline usando validação sem vazamento.', 'https://scikit-learn.org/stable/getting_started.html'),
    'Scikit-learn': ('Crie um Pipeline com pré-processamento e validação cruzada.', 'https://scikit-learn.org/stable/getting_started.html'),
    'Power BI': ('Crie um painel com medidas documentadas e filtros consistentes.', 'https://learn.microsoft.com/pt-br/power-bi/'),
    'AWS': ('Desenhe uma arquitetura para armazenar dados e executar um pipeline.', 'https://docs.aws.amazon.com/'),
    'Docker': ('Empacote uma API de previsão com dependências fixadas.', 'https://docs.docker.com/get-started/'),
    'LLMs': ('Compare respostas de um modelo de linguagem com uma lista de critérios explícitos.', 'https://huggingface.co/learn/llm-course/chapter1/1'),
    'RAG': ('Crie uma busca em documentos e avalie se as fontes recuperadas respondem à pergunta.', 'https://huggingface.co/learn/cookbook/en/advanced_rag'),
    'Git': ('Versione um projeto usando branches, commits pequenos e um README.', 'https://git-scm.com/book/pt-br/v2'),
    'Spark': ('Compare uma agregação local e uma execução com DataFrames do Spark.', 'https://spark.apache.org/docs/latest/'),
    'dbt': ('Documente transformações SQL e adicione testes de unicidade e valores nulos.', 'https://docs.getdbt.com/docs/introduction'),
    'Airflow': ('Orquestre um pipeline com tarefas idempotentes e tratamento de falhas.', 'https://airflow.apache.org/docs/'),
}


def learning_item(skill: str) -> dict:
    task, url = LEARNING.get(skill, (
        f'Adicione {skill} a um pequeno projeto, documente as escolhas e valide o resultado.', None))
    return {'task': task, 'url': url}
