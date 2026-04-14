import os
import sys
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if key in os.environ:
        del os.environ[key]

import json
import time
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Import our custom query logic and the ALREADY LOADED llm instance
from query_system import generate_answer, llm

load_dotenv()

# Share the same local LLM instance as the judge to save VRAM
judge_llm = llm

def ask_bot(question):
    """Obtains the answer from the RAG system"""
    try:
        # query_system.py's generate_answer handles retrieval internally
        final_answer = generate_answer(question)
        return final_answer
    except Exception as e:
        return f"Error: {str(e)}"

def evaluate_with_llm(question, expected, actual):
    judge_template = """Task: Compare 'Actual Answer' against 'Expected Answer' for NCU regulations.
    
    Question: {question}
    Expected Answer: {expected}
    Actual Answer: {actual}
    
    Grading Criteria:
    - PASS: The Actual Answer contains the same core fact or number as the Expected Answer.
    - FAIL: The Actual Answer is missing the fact, gives a different number, or says "I don't know".
    
    Output strictly ONLY the word 'PASS' or 'FAIL'. Do not explain.
    
    RESULT:"""
    
    prompt = PromptTemplate(template=judge_template, input_variables=["question", "expected", "actual"])
    chain = prompt | judge_llm
    
    try:
        result = chain.invoke({
            "question": question, 
            "expected": expected, 
            "actual": actual
        })
        
        # Local LLM (HuggingFacePipeline) returns a string directly, not a Message object
        result_text = result.strip()
        
        if "PASS" in result_text.upper():
            return "PASS"
        return "FAIL"
    except Exception as e:
        return f"FAIL (Judge Error: {str(e)})"

def run_llm_evaluation():
    try:
        with open("test_data.json", "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("❌ Error: test_data.json not found!")
        return

    print(f"🚀 Starting LLM-based Evaluation for {len(test_cases)} Questions...\n")
    
    passed_count = 0
    results_log = []

    for i, case in enumerate(test_cases):
        qid = case["id"]
        question = case["question"]
        expected_answer = case["answer"]
        
        print(f"Testing Q{qid}: {question}")
        
        start_time = time.time()
        bot_answer = ask_bot(question)
        
        verdict = evaluate_with_llm(question, expected_answer, bot_answer)
        duration = time.time() - start_time
        
        status_icon = "✅" if "PASS" in verdict else "❌"
        if "PASS" in verdict:
            passed_count += 1
            
        print(f"  -> Bot Says: {bot_answer.strip()}")
        print(f"  -> Judge: {status_icon} {verdict} (Time: {duration:.2f}s)")
        print("-" * 50)
        
        results_log.append({
            "id": qid,
            "question": question,
            "expected": expected_answer,
            "bot_response": bot_answer,
            "result": verdict
        })

    print("\n" + "="*30)
    print(f"📊 Evaluation Summary")
    print(f"Total: {len(test_cases)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(test_cases) - passed_count}")
    if len(test_cases) > 0:
        print(f"Accuracy: {(passed_count / len(test_cases)) * 100:.1f}%")
    print("="*30)

if __name__ == "__main__":
    run_llm_evaluation()