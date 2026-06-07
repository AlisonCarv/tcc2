import os
import sys

import pandas as pd
import psycopg2
from psycopg2 import extras


# =========================================================
# CONFIGURAÇÃO DE CAMINHOS
# =========================================================
# Estrutura esperada:
# PROJETO_TCC2/
# ├── data/
# └── src/
#     └── carga_postgres.py

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")


# =========================================================
# CONFIGURAÇÃO DO POSTGRESQL
# =========================================================
# As variáveis de ambiente são opcionais.
# Se não existirem, o script usará os valores padrão abaixo.

CONN_PARAMS = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DB", "olist_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "admin123"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


# Lista para rastrear falhas durante a carga
falhas = []


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


def load_table(file_name: str, table_name: str, columns: list[str]) -> None:
    """Carrega um arquivo CSV para uma tabela PostgreSQL."""
    file_full_path = verificar_arquivo(file_name)
    print(f"Processando arquivo: {file_name}...")

    conn = None

    try:
        df = pd.read_csv(file_full_path)
        df = df[columns]

        conn = psycopg2.connect(**CONN_PARAMS)
        cur = conn.cursor()

        cols = ",".join(columns)
        values = ",".join(["%s"] * len(columns))

        insert_query = (
            f"INSERT INTO {table_name} ({cols}) "
            f"VALUES ({values}) "
            f"ON CONFLICT DO NOTHING"
        )

        extras.execute_batch(cur, insert_query, df.values)
        conn.commit()

        print(f"   -> SUCESSO: {len(df)} registros carregados em '{table_name}'.")

        cur.close()

    except Exception as e:
        print(f"   -> [ERRO CRÍTICO] Falha ao carregar {table_name}: {e}")
        falhas.append(table_name)

    finally:
        if conn:
            conn.close()


def main() -> None:
    verificar_pasta_data()

    print("=== Iniciando ETL: Protótipo A (Relacional/PostgreSQL) ===")
    print(f"Pasta base do projeto: {BASE_DIR}")
    print(f"Pasta de dados: {DATA_PATH}")
    print("=" * 60)

    # Ordem de carga respeitando dependências por chaves estrangeiras
    load_table(
        "olist_customers_dataset.csv",
        "clientes",
        ["customer_id", "customer_unique_id", "customer_city"],
    )

    load_table(
        "olist_products_dataset.csv",
        "produtos",
        ["product_id", "product_category_name"],
    )

    load_table(
        "olist_sellers_dataset.csv",
        "vendedores",
        ["seller_id", "seller_city"],
    )

    load_table(
        "olist_orders_dataset.csv",
        "pedidos",
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
    )

    load_table(
        "olist_order_items_dataset.csv",
        "itens_pedido",
        ["order_id", "product_id", "seller_id", "price"],
    )

    print("\n" + "=" * 60)

    if not falhas:
        print("ETL CONCLUÍDO COM SUCESSO!")
        print("O banco relacional está íntegro e pronto para o benchmark.")
    else:
        print(f"ATENÇÃO: O processo terminou com erros nas tabelas: {', '.join(falhas)}")
        print("Verifique os logs acima antes de prosseguir para o benchmark.")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()