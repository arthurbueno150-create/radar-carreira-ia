# Origem e uso dos dados

**Fonte:** [Jobicy — API pública e condições de uso](https://jobicy.com/jobs-rss-feed).

**Documentação:** [Jobicy/remote-jobs-api](https://github.com/Jobicy/remote-jobs-api).

A fonte permite integrações, ferramentas de pesquisa e produtos de descoberta de vagas, com atribuição ao Jobicy e preservação da URL canônica. O aplicativo mantém o nome da fonte e o link de cada anúncio. Conteúdo de terceiros não recebe a licença MIT do código deste projeto.

Foram consultados estes endpoints públicos, sem autenticação:

- `https://jobicy.com/api/v2/remote-jobs?count=200&industry=data-science`
- `https://jobicy.com/api/v2/remote-jobs?count=200&industry=engineering`

Os slugs foram verificados no endpoint de taxonomias `?get=industries`. A amostra inclui até 200 registros por categoria, conforme a disponibilidade da fonte no momento da consulta. A base inclui título, empresa, restrição geográfica, categoria e nível informados pelo Jobicy, data de publicação, descrição limpa, competências derivadas e URL original. Não há coleta de dados privados de candidatos.

## Tratamento

1. Converter HTML em texto e ignorar scripts/estilos.
2. Exigir título, descrição e URL HTTPS no domínio do Jobicy.
3. Remover duplicatas por ID ou hash de empresa + título + descrição normalizados.
4. Extrair competências por vocabulário auditável com aliases.
5. Ordenar por publicação e calcular SHA-256 do conjunto tratado.
6. Guardar data de coleta, endpoints e contagens nos metadados.

As descrições podem mencionar tecnologias opcionais, desejáveis ou fora dos requisitos. O método não diferencia essas situações. Níveis e localidades vêm da fonte e não são inferidos pelo modelo. O app não traduz os anúncios nem converte salários. A associação à categoria vem da taxonomia do Jobicy, não de uma classificação humana feita para este projeto.

## Atualização e limitações

Use `python collect.py` para renovar a base, no máximo uma vez a cada seis horas. A consulta não acontece ao abrir ou usar o aplicativo. A fonte pode mudar seus campos, condições, cobertura e disponibilidade; confira a documentação antes de adaptações ou uso em produção.

Não interprete essa fotografia como série histórica, levantamento estatístico representativo ou lista garantidamente atual de vagas abertas. Uma interface local facilita estudar o problema; uma operação pública exigiria validação de atualidade, monitoramento e revisão das condições da fonte.
