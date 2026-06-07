import pandas as pd
import psycopg2
from psycopg2 import extras
import os
import sys

# CONFIGURAÇÃO DE ACESSO
conn_params = {
    "host": "localhost",
    "database": "olist_db",
    "user": "postgres",
    "password": "admin123" 
}

base_dir = r'D:\Álison\Faculdade\8º\TCC2\Projeto_TCC2'
data_path = os.path.join(base_dir, 'data')

# Lista para rastrear falhas
falhas = []

def load_table(file_name, table_name, columns):
    file_full_path = os.path.join(data_path, file_name)
    print(f"Processando arquivo: {file_name}...")
    
    conn = None
    try:
        df = pd.read_csv(file_full_path)
        df = df[columns] 
        
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        cols = ",".join(columns)
        values = ",".join(["%s"] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({cols}) VALUES ({values}) ON CONFLICT DO NOTHING"
        
        extras.execute_batch(cur, insert_query, df.values)
        conn.commit()
        
        print(f"   -> SUCESSO: {len(df)} registros em '{table_name}'.")
        cur.close()
    except Exception as e:
        print(f"   -> [ERRO CRÍTICO] Falha ao carregar {table_name}: {e}")
        falhas.append(table_name)
    finally:
        if conn:
            conn.close()

print("=== Iniciando ETL: Protótipo A (Relacional) ===")

# Ordem de carga respeitando as Foreign Keys [cite: 920-921]
load_table('olist_customers_dataset.csv', 'clientes', ['customer_id', 'customer_unique_id', 'customer_city'])
load_table('olist_products_dataset.csv', 'produtos', ['product_id', 'product_category_name'])
load_table('olist_sellers_dataset.csv', 'vendedores', ['seller_id', 'seller_city'])
load_table('olist_orders_dataset.csv', 'pedidos', ['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp'])
load_table('olist_order_items_dataset.csv', 'itens_pedido', ['order_id', 'product_id', 'seller_id', 'price'])

print("\n" + "="*40)
if not falhas:
    print("ETL CONCLUÍDO COM SUCESSO!")
    print("O banco relacional está íntegro e pronto para o benchmark.")
else:
    print(f"ATENÇÃO: O processo terminou com erros nas tabelas: {', '.join(falhas)}")
    print("Verifique os logs acima antes de prosseguir para o Neo4j.")
    sys.exit(1) # Finaliza o script com código de erro
print("="*40)