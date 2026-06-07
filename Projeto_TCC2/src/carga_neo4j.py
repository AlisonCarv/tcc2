import pandas as pd
from neo4j import GraphDatabase
import os
import time

# CONFIGURAÇÕES DE AMBIENTE [cite: 302]
uri = "bolt://localhost:7687"
user = "neo4j"
password = "admin123"
data_path = r'D:\Álison\Faculdade\8º\TCC2\Projeto_TCC2\data'

class Neo4jCarga:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def preparar_e_carregar(self):
        with self.driver.session() as session:
            # Limpeza de dados para garantir RNF02 [cite: 358, 441]
            print("Limpando dados existentes...")
            session.run("MATCH (n) DETACH DELETE n")

            # Criação de Constraints (Equivalente às PKs do Postgres) 
            print("Configurando restrições de integridade...")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cliente) REQUIRE c.customer_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Pedido) REQUIRE p.order_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Produto) REQUIRE pr.product_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vendedor) REQUIRE v.seller_id IS UNIQUE")

            # 1. CARGA DE CLIENTES
            print("Carregando Clientes...")
            df_c = pd.read_csv(os.path.join(data_path, 'olist_customers_dataset.csv'))[['customer_id', 'customer_city']]
            session.run("UNWIND $data AS row CREATE (:Cliente {customer_id: row.customer_id, cidade: row.customer_city})", data=df_c.to_dict('records'))

            # 2. CARGA DE VENDEDORES
            print("Carregando Vendedores...")
            df_v = pd.read_csv(os.path.join(data_path, 'olist_sellers_dataset.csv'))[['seller_id', 'seller_city']]
            session.run("UNWIND $data AS row CREATE (:Vendedor {seller_id: row.seller_id, cidade: row.seller_city})", data=df_v.to_dict('records'))

            # 3. CARGA DE PRODUTOS
            print("Carregando Produtos...")
            df_p = pd.read_csv(os.path.join(data_path, 'olist_products_dataset.csv'))[['product_id', 'product_category_name']]
            session.run("UNWIND $data AS row CREATE (:Produto {product_id: row.product_id, categoria: row.product_category_name})", data=df_p.to_dict('records'))

            # 4. CARGA DE PEDIDOS E RELAÇÃO [:FEZ_PEDIDO] (Figura 7) [cite: 403, 405]
            print("Processando Relação Cliente -> Pedido...")
            df_o = pd.read_csv(os.path.join(data_path, 'olist_orders_dataset.csv'))[['order_id', 'customer_id']]
            session.run("""
                UNWIND $data AS row
                MATCH (c:Cliente {customer_id: row.customer_id})
                CREATE (c)-[:FEZ_PEDIDO]->(p:Pedido {order_id: row.order_id})
            """, data=df_o.to_dict('records'))

            # 5. RELAÇÕES [:CONTEM] E [:VENDIDO_POR] (Figura 7) [cite: 407, 409]
            print("Processando Relações Pedido -> Produto -> Vendedor...")
            df_i = pd.read_csv(os.path.join(data_path, 'olist_order_items_dataset.csv'))[['order_id', 'product_id', 'seller_id', 'price']]
            batch_size = 5000
            for i in range(0, len(df_i), batch_size):
                batch = df_i.iloc[i:i+batch_size].to_dict('records')
                session.run("""
                    UNWIND $data AS row
                    MATCH (o:Pedido {order_id: row.order_id})
                    MATCH (p:Produto {product_id: row.product_id})
                    MATCH (v:Vendedor {seller_id: row.seller_id})
                    MERGE (o)-[:CONTEM {preco: row.price}]->(p)
                    MERGE (p)-[:VENDIDO_POR]->(v)
                """, data=batch)

if __name__ == "__main__":
    start_time = time.time()
    carga = Neo4jCarga(uri, user, password)
    carga.preparar_e_carregar()
    carga.close()
    print(f"\nCARGA CONCLUÍDA EM {round(time.time() - start_time, 2)}s")