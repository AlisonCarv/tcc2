import psycopg2
from neo4j import GraphDatabase
import time
import numpy as np
import pandas as pd
import sys
import random

# CONFIGURAÇÕES
POSTGRES_CONFIG = {"host": "localhost", "database": "olist_db", "user": "postgres", "password": "admin123"}
NEO4J_CONFIG = {"uri": "bolt://localhost:7687", "user": "neo4j", "password": "admin123"}

# ---------------------------------------------------------
# DICIONÁRIO DE CONSULTAS (BASE + STRESS + SHORTEST PATH)
# ---------------------------------------------------------
QUERIES = {
    "Q1": { # Filtragem Colaborativa Simples
        "sql": "SELECT p2.product_id, COUNT(p2.product_id) AS freq FROM itens_pedido i1 JOIN pedidos o1 ON i1.order_id = o1.order_id JOIN clientes c ON o1.customer_id = c.customer_id JOIN pedidos o2 ON c.customer_id = o2.customer_id JOIN itens_pedido i2 ON o2.order_id = i2.order_id JOIN produtos p2 ON i2.product_id = p2.product_id WHERE i1.product_id = %s AND i2.product_id <> %s GROUP BY p2.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (p1:Produto {product_id: $pid})<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(c:Cliente)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p2:Produto) WHERE p1 <> p2 RETURN p2.product_id, COUNT(p2) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "product"
    },
    "Q2": { # Produtos Frequentemente Comprados Juntos
        "sql": "SELECT i2.product_id, COUNT(*) AS freq FROM itens_pedido i1 JOIN itens_pedido i2 ON i1.order_id = i2.order_id WHERE i1.product_id = %s AND i2.product_id <> %s GROUP BY i2.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (p1:Produto {product_id: $pid})<-[:CONTEM]-(o:Pedido)-[:CONTEM]->(p2:Produto) WHERE p1 <> p2 RETURN p2.product_id, COUNT(*) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "product"
    },
    "Q3": { # Recomendação por Perfil Similar
        "sql": "SELECT p_target.product_id, COUNT(*) as freq FROM clientes c1 JOIN clientes c2 ON c1.customer_city = c2.customer_city JOIN pedidos o2 ON c2.customer_id = o2.customer_id JOIN itens_pedido i2 ON o2.order_id = i2.order_id JOIN produtos p_target ON i2.product_id = p_target.product_id WHERE c1.customer_id = %s AND c1.customer_id <> c2.customer_id AND p_target.product_category_name IN (SELECT DISTINCT pr.product_category_name FROM pedidos o1 JOIN itens_pedido i1 ON o1.order_id = i1.order_id JOIN produtos pr ON i1.product_id = pr.product_id WHERE o1.customer_id = %s) GROUP BY p_target.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (c1:Cliente {customer_id: $cid})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p1:Produto) WITH c1, collect(DISTINCT p1.categoria) AS categorias_alvo MATCH (c2:Cliente {cidade: c1.cidade})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p2:Produto) WHERE c1 <> c2 AND p2.categoria IN categorias_alvo RETURN p2.product_id, COUNT(p2) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "customer"
    },
    "Q4_G1": { # Teste Escalonado - Grau 1
        "sql": "SELECT p.product_id, COUNT(*) AS freq FROM pedidos o JOIN itens_pedido i ON o.order_id = i.order_id JOIN produtos p ON i.product_id = p.product_id WHERE o.customer_id = %s GROUP BY p.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (c:Cliente {customer_id: $cid})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p:Produto) RETURN p.product_id, COUNT(*) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "customer"
    },
    "Q4_G2": { # Teste Escalonado - Grau 2
        "sql": "SELECT p_rec.product_id, COUNT(*) AS freq FROM pedidos o1 JOIN itens_pedido i1 ON o1.order_id = i1.order_id JOIN itens_pedido i2 ON i1.product_id = i2.product_id JOIN pedidos o2 ON i2.order_id = o2.order_id JOIN pedidos o3 ON o2.customer_id = o3.customer_id JOIN itens_pedido i3 ON o3.order_id = i3.order_id JOIN produtos p_rec ON i3.product_id = p_rec.product_id WHERE o1.customer_id = %s AND o2.customer_id <> %s GROUP BY p_rec.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (c:Cliente {customer_id: $cid})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro:Cliente) MATCH (outro)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p_rec:Produto) WHERE c <> outro RETURN p_rec.product_id, COUNT(*) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "customer"
    },
    "Q4_G3": { # Teste Escalonado - Grau 3 (10 JOINs)
        "sql": "SELECT p_final.product_id, COUNT(*) AS freq FROM pedidos o1 JOIN itens_pedido i1 ON o1.order_id = i1.order_id JOIN itens_pedido i2 ON i1.product_id = i2.product_id JOIN pedidos o2 ON i2.order_id = o2.order_id JOIN pedidos o3 ON o2.customer_id = o3.customer_id JOIN itens_pedido i3 ON o3.order_id = i3.order_id JOIN itens_pedido i4 ON i3.product_id = i4.product_id JOIN pedidos o4 ON i4.order_id = o4.order_id JOIN pedidos o5 ON o4.customer_id = o5.customer_id JOIN itens_pedido i5 ON o5.order_id = i5.order_id JOIN produtos p_final ON i5.product_id = p_final.product_id WHERE o1.customer_id = %s AND o2.customer_id <> %s AND o4.customer_id <> %s GROUP BY p_final.product_id ORDER BY freq DESC LIMIT 10;",
        "cypher": "MATCH (c:Cliente {customer_id: $cid})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro1:Cliente) MATCH (outro1)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro2:Cliente) MATCH (outro2)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p_final:Produto) WHERE c <> outro1 AND outro1 <> outro2 AND c <> outro2 RETURN p_final.product_id, COUNT(*) AS freq ORDER BY freq DESC LIMIT 10;",
        "type": "customer"
    },
    "Q4_G4": { # A BOMBA COMBINATÓRIA - Grau 4 (14 JOINs)
        "sql": """
            SELECT p_final.product_id, COUNT(*) AS freq
            FROM pedidos o1 JOIN itens_pedido i1 ON o1.order_id = i1.order_id JOIN itens_pedido i2 ON i1.product_id = i2.product_id
            JOIN pedidos o2 ON i2.order_id = o2.order_id JOIN pedidos o3 ON o2.customer_id = o3.customer_id
            JOIN itens_pedido i3 ON o3.order_id = i3.order_id JOIN itens_pedido i4 ON i3.product_id = i4.product_id
            JOIN pedidos o4 ON i4.order_id = o4.order_id JOIN pedidos o5 ON o4.customer_id = o5.customer_id
            JOIN itens_pedido i5 ON o5.order_id = i5.order_id JOIN itens_pedido i6 ON i5.product_id = i6.product_id
            JOIN pedidos o6 ON i6.order_id = o6.order_id JOIN pedidos o7 ON o6.customer_id = o7.customer_id
            JOIN itens_pedido i7 ON o7.order_id = i7.order_id JOIN produtos p_final ON i7.product_id = p_final.product_id
            WHERE o1.customer_id = %s AND o2.customer_id <> %s AND o4.customer_id <> %s AND o6.customer_id <> %s
            GROUP BY p_final.product_id ORDER BY freq DESC LIMIT 10;
        """,
        "cypher": """
            MATCH (c:Cliente {customer_id: $cid})-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro1:Cliente)
            MATCH (outro1)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro2:Cliente)
            MATCH (outro2)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(:Produto)<-[:CONTEM]-(:Pedido)<-[:FEZ_PEDIDO]-(outro3:Cliente)
            MATCH (outro3)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(p_final:Produto)
            WHERE c <> outro1 AND outro1 <> outro2 AND outro2 <> outro3 AND c <> outro2 AND c <> outro3 AND outro1 <> outro3
            RETURN p_final.product_id, COUNT(*) AS freq ORDER BY freq DESC LIMIT 10;
        """,
        "type": "customer"
    },
    "Q5": { # O CAMINHO MAIS CURTO (Shortest Path vs CTE Recursiva)
        "sql": """
            WITH RECURSIVE rede(customer_id, depth) AS (
                SELECT %s::varchar, 0
                UNION
                SELECT o2.customer_id, r.depth + 1
                FROM rede r
                JOIN pedidos o1 ON r.customer_id = o1.customer_id
                JOIN itens_pedido i1 ON o1.order_id = i1.order_id
                JOIN itens_pedido i2 ON i1.product_id = i2.product_id
                JOIN pedidos o2 ON i2.order_id = o2.order_id
                WHERE r.depth < 4
            )
            SELECT MIN(depth) FROM rede WHERE customer_id = %s;
        """,
        "cypher": """
            MATCH p=shortestPath((c1:Cliente {customer_id: $cid1})-[*1..10]-(c2:Cliente {customer_id: $cid2}))
            RETURN length(p) AS saltos LIMIT 1;
        """,
        "type": "dual_customer" # Requer 2 clientes diferentes
    }
}

def get_seed_data(target):
    customers, products = [], []
    print(f"\n[{target.upper()}] Sorteando amostras dinâmicas...")
    
    if target == "postgres":
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT p.customer_id FROM pedidos p JOIN itens_pedido i ON p.order_id = i.order_id GROUP BY p.customer_id HAVING COUNT(i.product_id) > 1 LIMIT 20;")
        customers = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT product_id FROM itens_pedido GROUP BY product_id HAVING COUNT(order_id) > 5 LIMIT 20;")
        products = [row[0] for row in cur.fetchall()]
        conn.close()
    elif target == "neo4j":
        driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
        with driver.session() as session:
            res_c = session.run("MATCH (c:Cliente)-[:FEZ_PEDIDO]->(:Pedido)-[:CONTEM]->(pr:Produto) WITH c, COUNT(pr) AS qtd WHERE qtd > 1 RETURN c.customer_id LIMIT 20")
            customers = [record["c.customer_id"] for record in res_c]
            res_p = session.run("MATCH (p:Produto)<-[:CONTEM]-(o:Pedido) WITH p, COUNT(o) AS qtd WHERE qtd > 5 RETURN p.product_id LIMIT 20")
            products = [record["p.product_id"] for record in res_p]
        driver.close()
        
    if len(customers) < 2: customers = ["06b8899e6c202ee21f95ad3c7593c5d8", "18955e83d337fd6b2def6b18a428ac77"]
    if not products: products = ["e51273d3a90349f7e5f3089d4d12521f"]
    return customers, products

def run_benchmark(target, iterations=50, warm_up=5):
    customers, products = get_seed_data(target)
    results = []
    
    print(f"\n--- INICIANDO BENCHMARK ESTRUTURADO: {target.upper()} ---")
    print(f"Parâmetros: {warm_up} Warm-up | {iterations} Iterações (Max 10 para Estresse Profundo).")
    print("-" * 65)

    if target == "postgres":
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 120000;")
        
        for q_id, q_data in QUERIES.items():
            print(f"[{target.upper()}] Processando {q_id}...", end="", flush=True)
            times = []
            actual_iterations = min(iterations, 10) if q_id in ["Q4_G4", "Q5"] else iterations
            erro_critico = False
            
            for i in range(actual_iterations + warm_up):
                if q_data["type"] == "dual_customer":
                    seed1, seed2 = random.sample(customers, 2)
                    params = (seed1, seed2)
                else:
                    seed = random.choice(customers) if q_data["type"] == "customer" else random.choice(products)
                    params = (seed, seed) if q_id in ["Q1", "Q2", "Q3", "Q4_G2"] else ((seed, seed, seed) if q_id == "Q4_G3" else ((seed, seed, seed, seed) if q_id == "Q4_G4" else (seed,)))
                
                try:
                    start = time.perf_counter()
                    cur.execute(q_data["sql"], params)
                    cur.fetchall()
                    end = time.perf_counter()
                    if i >= warm_up: times.append((end - start) * 1000)
                except Exception as e:
                    print(f" [FALHA/TIMEOUT]")
                    conn.rollback()
                    erro_critico = True
                    break
            
            if erro_critico:
                results.append({"Banco": "PostgreSQL", "Consulta": q_id, "Media_ms": np.nan, "Desvio_ms": np.nan})
            else:
                print(f" Concluído! Média: {np.mean(times):.2f} ms")
                results.append({"Banco": "PostgreSQL", "Consulta": q_id, "Media_ms": np.mean(times), "Desvio_ms": np.std(times)})
        conn.close()

    elif target == "neo4j":
        driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
        with driver.session() as session:
            for q_id, q_data in QUERIES.items():
                print(f"[{target.upper()}] Processando {q_id}...", end="", flush=True)
                times = []
                actual_iterations = min(iterations, 10) if q_id in ["Q4_G4", "Q5"] else iterations
                erro_critico = False
                
                for i in range(actual_iterations + warm_up):
                    if q_data["type"] == "dual_customer":
                        seed1, seed2 = random.sample(customers, 2)
                        c_params = {"cid1": seed1, "cid2": seed2}
                    else:
                        seed = random.choice(customers) if q_data["type"] == "customer" else random.choice(products)
                        c_params = {"cid": seed} if q_data["type"] == "customer" else {"pid": seed}
                    
                    try:
                        start = time.perf_counter()
                        list(session.run(q_data["cypher"], **c_params))
                        end = time.perf_counter()
                        if i >= warm_up: times.append((end - start) * 1000)
                    except Exception as e:
                        print(f" [FALHA JVM]")
                        erro_critico = True
                        break
                
                if erro_critico:
                    results.append({"Banco": "Neo4j", "Consulta": q_id, "Media_ms": np.nan, "Desvio_ms": np.nan})
                else:
                    print(f" Concluído! Média: {np.mean(times):.2f} ms")
                    results.append({"Banco": "Neo4j", "Consulta": q_id, "Media_ms": np.mean(times), "Desvio_ms": np.std(times)})
        driver.close()
        
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    target = sys.argv[1].lower()
    df = pd.DataFrame(run_benchmark(target))
    df.to_csv(f"resultado_final_{target}.csv", index=False)
    
    print("\n" + "=" * 65)
    print(f"   RELATÓRIO CIENTÍFICO FINAL: {target.upper()}")
    print("=" * 65)
    print(df.to_string(index=False))
    print("=" * 65)