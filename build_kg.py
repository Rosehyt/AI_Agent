import sqlite3
from neo4j import GraphDatabase
import os
import re
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

def build_graph():
    sql_conn = sqlite3.connect("ncu_regulations.db")
    cursor = sql_conn.cursor()
    driver = GraphDatabase.driver(URI, auth=AUTH)

    print("Building Knowledge Graph (NCU Regulations)...")

    with driver.session() as session:
        # Clear existing data and legacy constraints
        session.run("MATCH (n) DETACH DELETE n")
        try:
            session.run("DROP CONSTRAINT article_number IF EXISTS")
        except:
            pass

        # ==========================================
        # Step 1: Create Fulltext Indexes (Requirement)
        # ==========================================
        print("  Index: Creating full-text indexes...")
        session.run("CREATE FULLTEXT INDEX article_content_idx IF NOT EXISTS FOR (n:Article) ON EACH [n.content]")
        session.run("CREATE FULLTEXT INDEX rule_idx IF NOT EXISTS FOR (n:Rule) ON EACH [n.action, n.result]")

        # ==========================================
        # Step 2: Create Regulation Nodes
        # ==========================================
        print("  Nodes: Importing Regulations...")
        cursor.execute("SELECT reg_id, name, category FROM regulations")
        regs = cursor.fetchall()
        reg_map = {} # Map ID to name for Article properties
        for r in regs:
            reg_id, reg_name, reg_category = r
            reg_map[reg_id] = (reg_name, reg_category)
            
            cypher_regulation = """
            MERGE (r:Regulation {id: $rid})
            SET r.name = $name, r.category = $cat
            """
            session.run(cypher_regulation, rid=reg_id, name=reg_name, cat=reg_category)

        # ==========================================
        # Step 3: Create Article & Rule Nodes
        # ==========================================
        print("  Nodes: Importing Articles & Extracting Rules...")
        cursor.execute("SELECT reg_id, article_number, content FROM articles")
        arts = cursor.fetchall()
        
        art_count = 0
        rule_count = 0
        
        for a in arts:
            reg_id, art_num, content = a
            reg_name, reg_category = reg_map.get(reg_id, ("Unknown", "Uncategorized"))
            
            # Create Article node with full properties (Requirement)
            cypher_article = """
            MATCH (r:Regulation {id: $rid})
            CREATE (a:Article {
                number: $num, 
                content: $content,
                reg_name: $reg_name,
                category: $category
            })
            MERGE (r)-[:HAS_ARTICLE]->(a)
            RETURN id(a) as internal_id
            """
            res = session.run(cypher_article, 
                        rid=reg_id, num=art_num, content=content, 
                        reg_name=reg_name, category=reg_category)
            art_internal_id = res.single()["internal_id"]
            art_count += 1

            # ==========================================
            # Sub-step: Extraction of Rule Nodes
            # ==========================================
            # Logic: Split content by numbered items (e.g., "(1)", "1.", "I.")
            # This follows the "Extract rule-level facts" requirement.
            rule_chunks = re.split(r'(\([0-9]+\)|[0-9]+\.)', content)
            
            # Reconstruct rules from chunks
            current_rule_text = ""
            extracted_rules = []
            
            if len(rule_chunks) <= 1:
                # If no numbering found, the whole article is one rule
                extracted_rules.append(content)
            else:
                # First chunk might be preamble, we skip or add to first rule
                for i in range(1, len(rule_chunks), 2):
                    num = rule_chunks[i]
                    text = rule_chunks[i+1] if i+1 < len(rule_chunks) else ""
                    extracted_rules.append(f"{num} {text.strip()}")

            for i, rule_text in enumerate(extracted_rules):
                # Basic parsing for action/result (Heuristic)
                # In a real app, we might use an LLM here, but for construction we use text segments
                # For the assignment, we map the rule text to action/result as placeholders or segments
                action = rule_text[:len(rule_text)//2]
                result = rule_text[len(rule_text)//2:]
                
                rule_id = f"{art_num}-R{i+1}"
                
                cypher_rule = """
                MATCH (a:Article) WHERE id(a) = $art_id
                CREATE (rl:Rule {
                    rule_id: $rule_id,
                    type: 'Standard',
                    action: $action,
                    result: $result,
                    art_ref: $num,
                    reg_name: $reg_name
                })
                MERGE (a)-[:CONTAINS_RULE]->(rl)
                """
                session.run(cypher_rule, 
                            art_id=art_internal_id, 
                            rule_id=rule_id,
                            action=action,
                            result=result,
                            num=art_num,
                            reg_name=reg_name)
                rule_count += 1

    print("-" * 40)
    print("Success!")
    print(f"   Regulations: {len(regs)}")
    print(f"   Articles:    {art_count}")
    print(f"   Rules:       {rule_count}")
    print("-" * 40)
    
    driver.close()
    sql_conn.close()

if __name__ == "__main__":
    build_graph()