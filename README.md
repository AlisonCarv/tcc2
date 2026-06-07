# Comparação entre Modelagem Relacional e Modelagem em Grafos para Consultas de Recomendação em E-commerce

Este repositório contém os códigos, scripts, consultas, modelos de dados e documentação complementar desenvolvidos para o Trabalho de Conclusão de Curso intitulado:

**Comparação Prática entre Modelagem Relacional e Modelagem em Grafos para Consultas de Recomendação em E-commerce**

O objetivo do projeto é comparar, de forma prática, o desempenho e a expressividade entre uma abordagem relacional, utilizando **PostgreSQL**, e uma abordagem orientada a grafos, utilizando **Neo4j**, aplicadas a consultas de recomendação em um cenário de comércio eletrônico.

## Visão geral

Sistemas de recomendação em e-commerce dependem da análise de relações entre clientes, pedidos, produtos, vendedores e categorias. Tradicionalmente, essas informações são armazenadas em bancos relacionais, nos quais as conexões são reconstruídas por meio de junções entre tabelas.

Em contrapartida, bancos orientados a grafos representam essas conexões de forma explícita, permitindo consultas baseadas em travessias entre nós e relacionamentos.

Este projeto implementa e compara dois protótipos equivalentes:

- **Protótipo A:** modelo relacional em PostgreSQL, com tabelas normalizadas e índices B-Tree;
- **Protótipo B:** modelo de grafo em Neo4j, com nós, relacionamentos e propriedades no padrão *Labeled Property Graph*.

A comparação foi realizada por meio de um benchmark automatizado em Python, utilizando consultas representativas de sistemas de recomendação.

## Tecnologias utilizadas

- Python
- PostgreSQL
- Neo4j
- Cypher
- SQL
- Pandas
- NumPy
- Dataset público da Olist

## Dataset

Os arquivos de dados utilizados neste projeto pertencem ao conjunto público:

**Brazilian E-Commerce Public Dataset by Olist**

Por serem arquivos grandes, os dados não estão incluídos diretamente neste repositório. Para executar o projeto, é necessário baixar o dataset manualmente no Kaggle:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Após o download, extraia os arquivos `.csv` e coloque todos eles dentro da pasta `data/`, na raiz do projeto.

A pasta `data/` deve conter os seguintes arquivos:

```text
data/
├── olist_customers_dataset.csv
├── olist_geolocation_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

A presença desses arquivos é necessária para que os scripts de carga consigam localizar corretamente os dados da Olist.

## Estrutura do projeto

A estrutura esperada do projeto é:

```text
PROJETO_TCC2/
├── data/
│   ├── olist_customers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── product_category_name_translation.csv
│
├── src/
│   ├── benchmark.py
│   ├── carga_neo4j.py
│   ├── carga_postgres.py
│   ├── resultado_final_neo4j.csv
│   └── resultado_final_postgres.csv
│
├── requirements.txt
└── README.md
```

Os scripts principais estão na pasta `src/`:

- `carga_postgres.py`: realiza a carga dos dados no PostgreSQL;
- `carga_neo4j.py`: realiza a carga dos dados no Neo4j;
- `benchmark.py`: executa as consultas de benchmark nos dois bancos;
- `resultado_final_postgres.csv`: arquivo gerado com os resultados do PostgreSQL;
- `resultado_final_neo4j.csv`: arquivo gerado com os resultados do Neo4j.

## Consultas avaliadas

O benchmark foi estruturado a partir de cinco consultas principais:

| Consulta | Descrição |
|---|---|
| Q1 | Filtragem colaborativa simples |
| Q2 | Detecção de coocorrência de produtos no mesmo pedido |
| Q3 | Recomendação híbrida por perfil, geografia e categoria |
| Q4 | Teste de estresse com múltiplos saltos lógicos |
| Q5 | Descoberta de menor caminho entre entidades |

Essas consultas foram implementadas em SQL para o PostgreSQL e em Cypher para o Neo4j, respeitando a lógica de modelagem de cada paradigma.

## Modelagem relacional

No PostgreSQL, os dados foram estruturados em tabelas normalizadas, preservando entidades como clientes, pedidos, produtos, vendedores e itens de pedido. As associações são representadas por chaves primárias e estrangeiras.

Foram criados índices B-Tree sobre chaves e atributos utilizados em filtros, permitindo que o banco relacional executasse buscas indexadas antes das operações de junção.

Essa modelagem representa a abordagem tradicional de bancos relacionais, na qual os relacionamentos entre entidades são reconstruídos em tempo de consulta por meio de operações de `JOIN`.

## Modelagem em grafos

No Neo4j, as entidades principais foram representadas como nós, como:

- `:Cliente`
- `:Pedido`
- `:Produto`
- `:Vendedor`

As associações foram representadas como relacionamentos, como:

- `[:FEZ_PEDIDO]`
- `[:CONTEM]`
- `[:VENDIDO_POR]`
- `[:PERTENCE_A]`

A entidade associativa `itens_pedido`, presente no modelo relacional, foi incorporada ao relacionamento `[:CONTEM]`, preservando seus atributos como propriedades.

Essa modelagem permite que as consultas percorram diretamente os relacionamentos armazenados no grafo, favorecendo cenários de recomendação baseados em múltiplas conexões entre entidades.

## Benchmark

O benchmark foi desenvolvido em Python e executa as consultas nos dois bancos de dados, registrando os tempos de resposta para posterior comparação.

Entre os cuidados metodológicos adotados estão:

- execução de ciclos de aquecimento;
- amostragem dinâmica de chaves;
- repetição controlada das consultas;
- tratamento de timeouts;
- coleta de métricas de tempo de resposta;
- comparação quantitativa e qualitativa entre SQL e Cypher.

A amostragem dinâmica foi utilizada para reduzir o risco de viés por cache, evitando que as consultas fossem executadas sempre sobre os mesmos clientes ou produtos.

## Principais resultados

Os resultados indicaram que o PostgreSQL apresentou melhor desempenho em consultas rasas e seletivas, especialmente em cenários nos quais os índices B-Tree e o otimizador relacional conseguiram resolver as junções com baixa latência.

Por outro lado, o Neo4j apresentou melhor desempenho em consultas de maior profundidade, especialmente em cenários de travessia e descoberta de caminhos, nos quais a estrutura de grafo se mostrou mais adequada à navegação entre entidades conectadas.

Dessa forma, os resultados sugerem que o modelo relacional permanece altamente eficiente para consultas de baixa profundidade em bases de tamanho moderado, enquanto o modelo de grafos se torna especialmente adequado para consultas que exigem múltiplos saltos lógicos, descoberta de caminhos e análise de redes altamente conectadas.

## Requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3.10 ou superior;
- PostgreSQL;
- Neo4j;
- Git.

As dependências Python estão listadas no arquivo `requirements.txt`:

```txt
pandas
numpy
psycopg2-binary
neo4j
```

## Configuração dos bancos de dados

O projeto utiliza dois bancos de dados:

- PostgreSQL;
- Neo4j.

As credenciais padrão utilizadas pelos scripts são:

```python
POSTGRES_CONFIG = {
    "host": "localhost",
    "database": "olist_db",
    "user": "postgres",
    "password": "admin123",
    "port": "5432"
}

NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "admin123"
}
```

Caso o seu ambiente utilize outro usuário, senha ou nome de banco, você pode alterar as credenciais por variáveis de ambiente.

### Variáveis de ambiente aceitas

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=olist_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin123

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=admin123
```

Se nenhuma variável de ambiente for definida, os scripts utilizarão os valores padrão apresentados acima.

## Observação sobre caminhos dos arquivos

Os scripts foram configurados para usar caminhos relativos.

A estrutura recomendada é manter a pasta `data/` na raiz do projeto e os scripts dentro da pasta `src/`.

Exemplo:

```text
PROJETO_TCC2/
├── data/
└── src/
```

Com essa configuração, os scripts localizam automaticamente os arquivos CSV da Olist a partir da pasta raiz do projeto, sem necessidade de editar caminhos absolutos no código.

## Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio
```

### 2. Baixar o dataset

Baixe o dataset da Olist no Kaggle:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Depois, extraia os arquivos `.csv` e coloque todos eles dentro da pasta `data/`.

### 3. Criar ambiente virtual

```bash
python -m venv venv
```

No Windows:

```bash
venv\Scripts\activate
```

No Linux/macOS:

```bash
source venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Preparar o banco PostgreSQL

Antes de executar a carga, crie o banco de dados `olist_db` no PostgreSQL.

Também é necessário criar previamente as tabelas esperadas pelos scripts, conforme o modelo relacional desenvolvido no projeto.

As tabelas utilizadas pelo script de carga são:

- `clientes`
- `produtos`
- `vendedores`
- `pedidos`
- `itens_pedido`

### 6. Executar a carga no PostgreSQL

```bash
python src/carga_postgres.py
```

### 7. Executar a carga no Neo4j

Certifique-se de que o Neo4j esteja em execução e acessível em:

```text
bolt://localhost:7687
```

Depois execute:

```bash
python src/carga_neo4j.py
```

### 8. Executar o benchmark

Para executar o benchmark no PostgreSQL:

```bash
python src/benchmark.py postgres
```

Para executar o benchmark no Neo4j:

```bash
python src/benchmark.py neo4j
```

Ao final da execução, os resultados serão salvos em arquivos `.csv`, como:

```text
src/resultado_final_postgres.csv
src/resultado_final_neo4j.csv
```

## Documentação

Este repositório pode incluir materiais complementares do projeto, como:

- versão final do TCC;
- diagramas de modelagem;
- scripts SQL;
- scripts Cypher;
- consultas utilizadas no benchmark;
- resultados experimentais;
- documentação auxiliar.

## Autor

**Álison Christian Rebouças Vidal de Carvalho**  
Curso de Engenharia de Software  
Universidade Tecnológica Federal do Paraná — UTFPR  
Campus Cornélio Procópio

## Orientador

**Prof. Dr. Eduardo Cotrin Teixeira**

## Licença

Este projeto foi desenvolvido para fins acadêmicos. O uso, reprodução ou adaptação dos códigos e materiais deve citar a autoria original.

## Referência acadêmica

CARVALHO, Álison Christian Rebouças Vidal de. **Comparação prática entre modelagem relacional e modelagem em grafos para consultas de recomendação em e-commerce**. Trabalho de Conclusão de Curso — Engenharia de Software, Universidade Tecnológica Federal do Paraná, Cornélio Procópio, 2026.
