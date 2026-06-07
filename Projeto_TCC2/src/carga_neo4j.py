import os
import sys
import time

import pandas as pd
from neo4j import GraphDatabase


# =========================================================
# CONFIGURAÇÃO DE CAMINHOS
# =========================================================
# Estrutura esperada:
# PROJETO_TCC2/
# ├── data/
# └── src/
#     └── carga_neo4j.py

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")


# =========================================================
# CONFIGURAÇÃO DO NEO4J
# =========================================================
# As variáveis de ambiente são opcionais.
# Se não existirem, o script usará os valores padrão abaixo.

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "admin123")


def verificar_pasta_data() -> None:
    """Verifica se a pasta data existe."""
    if not os.path.isdir(DATA_PATH):
        print(f"[ERRO] Pasta de dados não encontrada: {DATA_PATH}")
        print("Baixe o dataset da Olist no Kaggle e coloque os arquivos CSV dentro da pasta data/.")
        sys.exit(1)


def verificar_arquivo(file_name: str) -> str:
    """Verifica se um arquivo CSV existe dentro da pasta data."""
    file_full_path = os.path.join(DATA_PATH, file_name)

    if not os.path.isfile(file_full_path):
        print(f"[ERRO] Arquivo não encontrado: {file_full_path}")
        print("Verifique se todos os arquivos CSV da Olist foram colocados corretamente na pasta data/.")
        sys.exit(1)

    return file_full_path


def enviar_em_lotes(session, query: str, dados: list[dict], tamanho_lote: int = 5000) -> None:
    """Envia dados para o Neo4j em lotes."""
    total = len(dados)

    for inicio in range(0, total, tamanho_lote):
        lote = dados[inicio:inicio + tamanho_lote]
        session.run(query, data=lote)
        print(f"   -> Lote {inicio + len(lote)}/{total} processado.")


class Neo4jCarga:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def preparar_e_carregar(self) -> None:
        with self.driver.session() as session:
            print("Limpando dados existentes...")
            session.run("MATCH (n) DETACH DELETE n")

            print("Configurando restrições de integridade...")
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS "
                "FOR (c:Cliente) REQUIRE c.customer_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS "
                "FOR (p:Pedido) REQUIRE p.order_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS "
                "FOR (pr:Produto) REQUIRE pr.product_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS "
                "FOR (v:Vendedor) REQUIRE v.seller_id IS UNIQUE"
            )

            # =================================================
            # 1. CARGA DE CLIENTES
            # =================================================
            print("\nCarregando Clientes...")
            df_c = pd.read_csv(verificar_arquivo("olist_customers_dataset.csv"))[
                ["customer_id", "customer_city"]
            ]

            enviar_em_lotes(
                session,
                """
                UNWIND $data AS row
                CREATE (:Cliente {
                    customer_id: row.customer_id,
                    cidade: row.customer_city
                })
                """,
                df_c.to_dict("records"),
            )

            # =================================================
            # 2. CARGA DE VENDEDORES
            # =================================================
            print("\nCarregando Vendedores...")
            df_v = pd.read_csv(verificar_arquivo("olist_sellers_dataset.csv"))[
                ["seller_id", "seller_city"]
            ]

            enviar_em_lotes(
                session,
                """
                UNWIND $data AS row
                CREATE (:Vendedor {
                    seller_id: row.seller_id,
                    cidade: row.seller_city
                })
                """,
                df_v.to_dict("records"),
            )

            # =================================================
            # 3. CARGA DE PRODUTOS
            # =================================================
            print("\nCarregando Produtos...")
            df_p = pd.read_csv(verificar_arquivo("olist_products_dataset.csv"))[
                ["product_id", "product_category_name"]
            ]

            enviar_em_lotes(
                session,
                """
                UNWIND $data AS row
                CREATE (:Produto {
                    product_id: row.product_id,
                    categoria: row.product_category_name
                })
                """,
                df_p.to_dict("records"),
            )

            # =================================================
            # 4. CARGA DE PEDIDOS E RELAÇÃO [:FEZ_PEDIDO]
            # =================================================
            print("\nProcessando relação Cliente -> Pedido...")
            df_o = pd.read_csv(verificar_arquivo("olist_orders_dataset.csv"))[
                ["order_id", "customer_id"]
            ]

            enviar_em_lotes(
                session,
                """
                UNWIND $data AS row
                MATCH (c:Cliente {customer_id: row.customer_id})
                CREATE (c)-[:FEZ_PEDIDO]->(:Pedido {
                    order_id: row.order_id
                })
                """,
                df_o.to_dict("records"),
            )

            # =================================================
            # 5. RELAÇÕES [:CONTEM] E [:VENDIDO_POR]
            # =================================================
            print("\nProcessando relações Pedido -> Produto -> Vendedor...")
            df_i = pd.read_csv(verificar_arquivo("olist_order_items_dataset.csv"))[
                ["order_id", "product_id", "seller_id", "price"]
            ]

            enviar_em_lotes(
                session,
                """
                UNWIND $data AS row
                MATCH (o:Pedido {order_id: row.order_id})
                MATCH (p:Produto {product_id: row.product_id})
                MATCH (v:Vendedor {seller_id: row.seller_id})
                MERGE (o)-[:CONTEM {preco: row.price}]->(p)
                MERGE (p)-[:VENDIDO_POR]->(v)
                """,
                df_i.to_dict("records"),
            )


def main() -> None:
    verificar_pasta_data()

    print("=== Iniciando ETL: Protótipo B (Grafo/Neo4j) ===")
    print(f"Pasta base do projeto: {BASE_DIR}")
    print(f"Pasta de dados: {DATA_PATH}")
    print("=" * 60)

    start_time = time.time()

    carga = Neo4jCarga(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        carga.preparar_e_carregar()
    finally:
        carga.close()

    print("\n" + "=" * 60)
    print(f"CARGA CONCLUÍDA EM {round(time.time() - start_time, 2)}s")
    print("=" * 60)


if __name__ == "__main__":
    main()