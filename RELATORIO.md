# Radar de Carreira IA — relatório do projeto

## Problema e proposta

Quem estuda dados encontra muitas tecnologias e nem sempre sabe qual aprender a seguir. Este projeto transforma uma amostra pública de vagas em evidências: competências mencionadas, grupos de vagas semelhantes, recomendações explicáveis e simulações de cobertura.

O diferencial é conectar **análise exploratória → recomendação → experimento de aprendizado**, com cálculos executados em Python e uma interface navegável. Não depende de uma API paga de IA.

## Base utilizada

- Fonte: [API pública do Jobicy](https://jobicy.com/jobs-rss-feed), com atribuição e links canônicos preservados.
- Coleta: 19/09/2026 no horário de Brasília; 20/09/2026 em UTC.
- 317 registros recebidos, 1 duplicata removida, **316 vagas únicas de 158 empresas**.
- 117 vagas na categoria Dados e analytics; 199 em Engenharia de software.
- 286 vagas com pelo menos uma competência reconhecida; 30 sem competência extraída.
- 53 competências diferentes reconhecidas na amostra.

Cada consulta retorna até 200 anúncios recentes da categoria. A coleta é uma amostra de conveniência de vagas remotas internacionais; não constitui levantamento representativo de todo o mercado ou do Brasil. O registro de coleta e o hash estão em `data/jobs.json`.

## Principais observações

Na amostra completa, **Python e SQL aparecem em 135 vagas cada (42,7%)**. APIs aparecem em 105 (33,2%) e AWS em 92 (29,1%). Ao menos uma menção ao conjunto de competências de IA/ML ocorre em 140 vagas (44,3%).

Esses números contam menções, não exigências obrigatórias. Não permitem concluir crescimento ao longo do tempo ou probabilidade de contratação. A fonte, as categorias escolhidas e a predominância de anúncios em inglês influenciam os resultados.

## Modelos e avaliação

### Recomendação explicável

O texto do perfil e dos anúncios é representado por TF-IDF. A afinidade combina 35% de similaridade textual por cosseno e 65% de cobertura de competências ponderada por IDF. O usuário vê competências cobertas e não cobertas, além dos dois componentes do índice.

Os pesos são definidos para o protótipo e não foram calibrados com contratações reais. Não há rótulos humanos de relevância candidato-vaga para avaliar este ranking. A extração de competências usa um vocabulário de regras, não um modelo generativo.

### Agrupamento exploratório

K-means foi ajustado sobre vetores normalizados de competências, comparando de 2 a 6 grupos. O maior silhouette por cosseno foi **0,1585, com k=6**. O valor relativamente baixo indica sobreposição entre grupos; as carreiras não formam classes rígidas.

Os grupos foram descritos pelas três competências mais frequentes em cada um. Vagas sem competências reconhecidas ficam em um grupo separado, sem participar do K-means. O mapa usa uma projeção SVD em duas dimensões, que retém aproximadamente 12,7% da variância. Portanto, o mapa é uma visualização aproximada, não uma reprodução fiel de todas as distâncias do modelo.

### Experimento supervisionado auxiliar

Pergunta: o texto de título e descrição permite prever a categoria atribuída pelo Jobicy?

Foram usados TF-IDF e regressão logística, comparados com um baseline que sempre prevê a categoria majoritária do treino. Um `GroupShuffleSplit` com semente 42 reservou 25% das empresas para teste. O resultado foi 223 vagas de 118 empresas no treino e 93 vagas de 40 empresas no teste. **Nenhuma empresa aparece nos dois conjuntos.** O vocabulário deste experimento é ajustado apenas no treino.

| Modelo | Acurácia no teste | Macro-F1 no teste |
|---|---:|---:|
| Classe majoritária | 73,12% | 0,4224 |
| TF-IDF + regressão logística | 90,32% | 0,8813 |

Matriz de confusão, com categoria real nas linhas:

| Real / prevista | Dados e analytics | Engenharia de software |
|---|---:|---:|
| Dados e analytics | 22 | 3 |
| Engenharia de software | 6 | 62 |

O modelo superou o baseline neste particionamento. O resultado não demonstra capacidade geral de seleção de candidatos: mede apenas a reprodução das categorias da fonte em um único teste separado por empresa. O experimento supervisionado não participa do ranking de recomendações.

## Simulador de aprendizado

O simulador adiciona competências ao perfil e recalcula a cobertura na **mesma população de vagas filtradas**. A similaridade textual permanece fixa. Vagas sem competências extraídas são excluídas da média de cobertura.

Para cada habilidade ausente, o plano calcula o ganho marginal médio se ela fosse adicionada. Sugestões de prática são ordenadas por esse ganho e mantêm links para documentação quando disponíveis. O ganho não incorpora dificuldade de aprendizado, horas de estudo, senioridade ou salários.

## Reproduzir e apresentar

1. Inicie com `INICIAR.bat` no Windows ou `python iniciar.py`.
2. Mostre as contagens e filtre a categoria Dados e analytics.
3. Abra Meu radar e informe somente competências que você conhece.
4. Analise o perfil e expanda uma recomendação para mostrar a explicação.
5. Adicione uma competência e compare a cobertura antes/depois.
6. Abra Laboratório ML e explique a distinção entre recomendação, clustering e classificação.

O notebook `notebooks/01_exploracao_e_modelagem.ipynb` contém seis células de código executadas, com saídas preservadas. Para refazer a avaliação: `python train.py`. Para verificar o projeto: `python -m pytest -q`. As 19 verificações automatizadas cobrem limpeza, limites de palavras, deduplicação, filtros, cálculo de afinidade, simulação, entradas inválidas, exportação e separação de empresas.

## Limites e evoluções possíveis

- O extrator pode confundir menções com domínio real, ignorar negações e deixar de reconhecer sinônimos fora do vocabulário.
- A recomendação não avalia senioridade nem elegibilidade geográfica; esses dados são apresentados para decisão do usuário.
- Uma avaliação do ranking exigiria perfis consentidos e julgamentos humanos de relevância.
- Analisar tendências exigiria coletas históricas comparáveis e controle da composição da fonte.
- Para medir variabilidade da classificação, uma etapa futura pode usar validação cruzada por empresa e teste temporal independente.

Referências de implementação: [TF-IDF no scikit-learn](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction), [K-means e clustering](https://scikit-learn.org/stable/modules/clustering.html#k-means) e [Flask](https://flask.palletsprojects.com/en/stable/).
