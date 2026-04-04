import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠️ Warning: GOOGLE_API_KEY not found in environment variables. Please check your .env file.")

DATA_FOLDER = "data"
DB_FOLDER = "chroma_db"

# 檔案對應
FILES = {
    "apple": "FY24_Q4_Consolidated_Financial_Statements.pdf",
    "tesla": "tsla-20241231-gen.pdf"
}

# ==============================================================================
# Embedding Model (自由切換版：可隨時修改)
# ==============================================================================
# 🔴 您可以在這裡將模型切換為 "baseline" (基礎輕量版) 或 "advanced" (進階聰明版)
ACTIVE_EMBEDDING = "advanced" 

if ACTIVE_EMBEDDING == "baseline":
    # 這是比較弱、但建檔較快的基礎模型
    LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    DB_FOLDER = "chroma_db_baseline" 
else:
    # 這是非常聰明、能夠看懂複雜財報的進階開源模型
    LOCAL_EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    DB_FOLDER = "chroma_db_advanced"

def get_embeddings():
    print(f"🔄 Loading [{ACTIVE_EMBEDDING.upper()}] Local Model: {LOCAL_EMBEDDING_MODEL}...")
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)

# ==============================================================================
# 3. LLM Model (All Students should use Gemini 2.0-flash)
# ==============================================================================
def get_llm(temperature=0):
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GOOGLE_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-001")
    
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
        max_tokens=2048,
        max_retries=0
    )
    return llm