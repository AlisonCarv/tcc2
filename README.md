# Análise Comparativa de Bancos de Dados Relacionais e Orientados a Grafos para Sistemas de Recomendação em E-commerce

Este repositório contém os códigos, scripts, consultas, modelos de dados e resultados experimentais desenvolvidos para o Trabalho de Conclusão de Curso intitulado:

**Análise Comparativa de Bancos de Dados Relacionais e Orientados a Grafos para Sistemas de Recomendação em E-commerce**

O objetivo do projeto é comparar o desempenho e a expressividade de consultas em dois modelos de banco de dados aplicados a um cenário de recomendação em e-commerce:

- **Modelo A:** modelo relacional implementado no PostgreSQL;
- **Modelo B:** modelo orientado a grafos implementado no Neo4j.

A comparação foi realizada por meio de scripts em Python, utilizando consultas equivalentes em SQL e Cypher sobre o conjunto de dados público da Olist.

---

## Visão geral

Sistemas de recomendação em e-commerce dependem da análise de relações entre clientes, pedidos, produtos, vendedores e categorias. No modelo relacional, essas relações são representadas por tabelas, chaves primárias, chaves estrangeiras e operações de junção. No modelo orientado a grafos, as mesmas relações são representadas por nós, relacionamentos e propriedades.

Este projeto implementa os dois modelos a partir da mesma base de dados e executa um benchmark com consultas de recomendação e análise de relacionamento. Os resultados permitem observar em quais cenários o PostgreSQL apresenta melhor desempenho e em quais situações o Neo4j se mostra mais adequado.

---

## Tecnologias utilizadas

- Python
- PostgreSQL
- Neo4j
- SQL
- Cypher
- pandas
- NumPy
- psycopg2
- neo4j-driver
- Dataset público da Olist

---

## Dataset

O projeto utiliza o conjunto público:

**Brazilian E-Commerce Public Dataset by Olist**

O dataset está disponível no Kaggle:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Os arquivos do dataset não estão incluídos neste repositório. Para executar o projeto, baixe o dataset no Kaggle, extraia os arquivos `.csv` e coloque-os na pasta `data/`, na raiz do projeto.

A pasta `data/` deve conter:

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

Os scripts deste projeto utilizam principalmente os arquivos de clientes, pedidos, itens de pedido, produtos e vendedores.

---

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
│   └── carga_postgres.py
│
├── resultado_final_neo4j.csv
├── resultado_final_postgres.csv
├── requirements.txt
└── README.md
```

Os arquivos `resultado_final_neo4j.csv` e `resultado_final_postgres.csv` são gerados após a execução do benchmark. Dependendo do diretório em que o comando for executado, eles podem ser salvos na raiz do projeto ou no diretório de execução.

---

## Scripts principais

| Script | Função |
|---|---|
| `carga_postgres.py` | Lê os arquivos CSV da Olist e carrega os dados no PostgreSQL. |
| `carga_neo4j.py` | Lê os arquivos CSV da Olist, cria nós e relacionamentos no Neo4j e aplica restrições de unicidade. |
| `benchmark.py` | Executa as consultas em PostgreSQL ou Neo4j, mede os tempos de resposta e gera arquivos CSV com os resultados. |

---

## Modelo relacional no PostgreSQL

No PostgreSQL, os dados são organizados em tabelas relacionadas por identificadores. As principais tabelas utilizadas são:

- `clientes`
- `pedidos`
- `produtos`
- `vendedores`
- `itens_pedido`

As relações entre as tabelas são mantidas por identificadores como:

- `customer_id`
- `order_id`
- `product_id`
- `seller_id`

A tabela `itens_pedido` atua como estrutura associativa entre pedidos, produtos e vendedores. Esse modelo permite executar as consultas em SQL por meio de operações de junção entre as tabelas.

---

## Modelo de grafo no Neo4j

No Neo4j, as entidades principais são representadas como nós:

- `:Cliente`
- `:Pedido`
- `:Produto`
- `:Vendedor`

As associações entre essas entidades são representadas por relacionamentos direcionados:

- `[:FEZ_PEDIDO]`: conecta um cliente a um pedido realizado;
- `[:CONTEM]`: conecta um pedido aos produtos contidos nele;
- `[:VENDIDO_POR]`: conecta um produto ao vendedor correspondente.

Atributos da associação entre pedido e produto, como `preco`, são armazenados como propriedades do relacionamento `[:CONTEM]`.

Esse modelo permite que consultas em Cypher percorram diretamente os relacionamentos armazenados no grafo.

---

## Consultas avaliadas

O benchmark foi estruturado com cinco grupos de consultas:

| Consulta | Objetivo |
|---|---|
| `Q1` | Recomendar produtos comprados por clientes que também compraram um produto de referência. |
| `Q2` | Identificar produtos frequentemente comprados no mesmo pedido. |
| `Q3` | Recomendar produtos com base em clientes da mesma cidade e categorias já consumidas. |
| `Q4_G1` a `Q4_G4` | Avaliar o impacto do aumento progressivo da profundidade das relações percorridas. |
| `Q5` | Encontrar o menor caminho entre dois clientes a partir das conexões formadas por pedidos e produtos. |

As consultas foram implementadas em SQL para o PostgreSQL e em Cypher para o Neo4j, respeitando a lógica de cada modelo.

---

## Procedimento de benchmark

O benchmark foi executado pelo script `benchmark.py`. O procedimento geral foi:

1. conectar-se ao banco selecionado;
2. selecionar identificadores existentes na base, como `customer_id` e `product_id`;
3. executar consultas equivalentes em SQL ou Cypher;
4. medir o tempo de execução com `time.perf_counter()`;
5. descartar execuções de aquecimento;
6. calcular média e desvio-padrão dos tempos;
7. registrar os resultados em arquivo CSV.

Foram utilizadas execuções de aquecimento para reduzir o efeito da primeira execução sobre os tempos registrados. As consultas mais custosas, como `Q4_G4` e `Q5`, tiveram menor número de repetições para evitar execuções excessivamente longas.

No PostgreSQL, foi utilizado o parâmetro `statement_timeout` para interromper consultas que ultrapassassem o limite definido no experimento.

---

## Principais resultados

Os resultados observados no experimento indicaram comportamentos distintos entre os dois bancos.

| Cenário | Resultado observado |
|---|---|
| Consultas de baixa profundidade | O PostgreSQL apresentou melhor desempenho em consultas como `Q1` e `Q2`. |
| Consulta híbrida por perfil e geografia | O Neo4j apresentou menor tempo médio na `Q3`. |
| Aumento progressivo de profundidade | O Neo4j concluiu a variação mais profunda da `Q4`, enquanto o PostgreSQL atingiu timeout. |
| Caminho mais curto entre clientes | O Neo4j apresentou menor tempo de execução e consulta mais direta em Cypher. |

De forma geral, o PostgreSQL mostrou-se eficiente em consultas com relações diretas e bem representadas por chaves e índices. O Neo4j apresentou melhor comportamento nos cenários que exigiram percorrer múltiplas relações ou descobrir caminhos entre entidades.

---

## Requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3.10 ou superior;
- PostgreSQL;
- Neo4j;
- Git.

As dependências Python estão listadas em `requirements.txt`:

```txt
pandas
numpy
psycopg2-binary
neo4j
```

Para instalar as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração dos bancos de dados

### PostgreSQL

O script `carga_postgres.py` utiliza, por padrão, as seguintes configurações:

```python
conn_params = {
    "host": "localhost",
    "database": "olist_db",
    "user": "postgres",
    "password": "admin123"
}
```

Antes de executar a carga, crie o banco de dados `olist_db` e as tabelas esperadas pelo modelo relacional.

As tabelas utilizadas pelo script são:

- `clientes`
- `produtos`
- `vendedores`
- `pedidos`
- `itens_pedido`

Caso seu ambiente utilize outro usuário, senha, host ou nome de banco, altere o dicionário `conn_params` no início do arquivo `src/carga_postgres.py`.

### Neo4j

O script `carga_neo4j.py` utiliza, por padrão:

```python
uri = "bolt://localhost:7687"
user = "neo4j"
password = "admin123"
```

Caso seu ambiente utilize outro usuário, senha ou endereço, altere essas variáveis no início do arquivo `src/carga_neo4j.py`.

---

## Configuração dos caminhos dos arquivos

Os scripts de carga precisam localizar a pasta `data/`.

Se o caminho local do projeto for diferente, ajuste as variáveis de caminho no início dos scripts:

- em `carga_postgres.py`, verifique `base_dir` e `data_path`;
- em `carga_neo4j.py`, verifique `data_path`.

Recomenda-se manter a estrutura:

```text
PROJETO_TCC2/
├── data/
└── src/
```

---

## Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio
```

### 2. Baixar e organizar o dataset

Baixe o dataset da Olist no Kaggle:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Extraia os arquivos `.csv` e coloque-os dentro da pasta `data/`.

### 3. Criar e ativar ambiente virtual

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

### 5. Preparar o PostgreSQL

Crie o banco de dados `olist_db` e as tabelas do modelo relacional.

Em seguida, execute:

```bash
python src/carga_postgres.py
```

### 6. Preparar o Neo4j

Certifique-se de que o Neo4j esteja em execução e acessível em:

```text
bolt://localhost:7687
```

Depois execute:

```bash
python src/carga_neo4j.py
```

### 7. Executar o benchmark

Para executar o benchmark no PostgreSQL:

```bash
python src/benchmark.py postgres
```

Para executar o benchmark no Neo4j:

```bash
python src/benchmark.py neo4j
```

Ao final, serão gerados arquivos CSV com os resultados:

```text
resultado_final_postgres.csv
resultado_final_neo4j.csv
```

---

## Saída dos resultados

Cada arquivo de resultado contém colunas semelhantes a:

```text
Banco,Consulta,Media_ms,Desvio_ms
```

Onde:

- `Banco`: banco avaliado;
- `Consulta`: consulta executada;
- `Media_ms`: tempo médio em milissegundos;
- `Desvio_ms`: desvio-padrão em milissegundos.

Quando uma consulta não é concluída dentro do limite definido, o resultado pode ser registrado sem média válida.

---

## Documentação complementar

Este repositório pode incluir materiais complementares, como:

- versão final do TCC;
- diagramas de modelagem;
- consultas SQL;
- consultas Cypher;
- arquivos de resultados experimentais;
- documentação auxiliar.

---

## Autor

**Álison Christian Rebouças Vidal de Carvalho**  
Curso de Engenharia de Software  
Universidade Tecnológica Federal do Paraná — UTFPR  
Campus Cornélio Procópio

---

## Orientador

**Prof. Dr. Eduardo Cotrin Teixeira**

---

## Referência acadêmica

CARVALHO, Álison Christian Rebouças Vidal de. **Análise Comparativa de Bancos de Dados Relacionais e Orientados a Grafos para Sistemas de Recomendação em E-commerce**. Trabalho de Conclusão de Curso — Engenharia de Software, Universidade Tecnológica Federal do Paraná, Cornélio Procópio, 2026.

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos. O uso, reprodução ou adaptação dos códigos e materiais deve citar a autoria original.
