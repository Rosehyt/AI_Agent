import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Import our custom local LLM loader
from llm_loader import load_local_llm

# Handle proxy issues if any
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if key in os.environ:
        del os.environ[key]

load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
except Exception as e:
    print(f"⚠️ Neo4j Connection Warning: {e}")

# Mandatory Local LLM Initialization (Qwen2.5-3B-Instruct)
llm = load_local_llm()

def get_retrieval_query(user_question):
    """
    Constructs a Cypher query for targeted retrieval.
    Requirement: "Better retrieval precision/recall (typed + broad query strategy)"
    
    Strategy: 
    1. Use Fulltext Search on 'rule_idx' to find the most relevant rules.
    2. Expand to parent 'Article' to get full context.
    """
    
    cypher = """
    CALL db.index.fulltext.queryNodes("rule_idx", $query) YIELD node, score
    MATCH (a:Article)-[:CONTAINS_RULE]->(node)
    RETURN 
        a.reg_name AS reg_name, 
        a.number AS art_num, 
        a.content AS art_content, 
        node.action AS rule_action, 
        node.result AS rule_result,
        score
    ORDER BY score DESC
    LIMIT 3
    """
    return cypher

def run_query(cypher, params):
    try:
        with driver.session() as session:
            return [record.data() for record in session.run(cypher, params)]
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return []

def generate_answer(question):
    # Retrieve top 5 relevant rules/articles
    context_data = run_query(get_retrieval_query(question), {"query": question})
    
    if not context_data:
        # Fallback: Try a broader search on article index if rule search fails
        fallback_cypher = """
        CALL db.index.fulltext.queryNodes("article_content_idx", $query) YIELD node, score
        RETURN 
            node.reg_name AS reg_name, 
            node.number AS art_num, 
            node.content AS art_content,
            score
        ORDER BY score DESC
        LIMIT 2
        """
        context_data = run_query(fallback_cypher, {"query": question})

    if not context_data:
        return "I cannot find specific information regarding this request in the current NCU regulations."

    # Format context for LLM
    context_text = ""
    for item in context_data:
        reg = item.get('reg_name', 'Unknown')
        art = item.get('art_num', 'N/A')
        text = item.get('art_content', '')
        context_text += f"SOURCE: [{reg}] {art}\nCONTENT: {text}\n---\n"

    # LLM Prompt Construction (Requirement: Cite Source)
    from langchain_core.prompts import PromptTemplate
    
    template = """You are a precise NCU Regulation Assistant.
    Answer the user question based ONLY on the provided context. 

    CONTEXT:
    {c}

    USER QUESTION: {q}

    INSTRUCTIONS:
    1. Answer the question directly and concisely.
    2. Cite the regulation (e.g., "[Regulation Name] Article X").
    3. Do not include introductory phrases like "As an expert..." or "According to the context...".
    4. Language: English.

    ANSWER:"""
    
    prompt = PromptTemplate(template=template, input_variables=["q", "c"])
    chain = prompt | llm
    
    try:
        # Note: Depending on context size, we might need to trim, 
        # but 5 rules + 3 articles should fit easily in Qwen's context.
        return chain.invoke({"q": question, "c": context_text[:8000]})
    except Exception as e:
        return f"LLM Error: {e}"

if __name__ == "__main__":
    print("="*50)
    print("🎓 NCU Regulation Assistant (Local AI Mode)")
    print("="*50)
    print("💡 Try: 'What are the rules for choosing a graduate advisor?'")
    print("👉 Type 'exit' to quit.\n")

    while True:
        try:
            user_q = input("\nUser: ").strip()
            if not user_q: continue
            if user_q.lower() in ['exit', 'quit']:
                break
            
            print("🤖 Analyzing Knowledge Graph...")
            answer = generate_answer(user_q)
            print(f"\nBot: {answer}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    driver.close()