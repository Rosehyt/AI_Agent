import os
from agent import ReActAgent

def run_assignment():
    agent = ReActAgent()
    
    tasks = [
        "What fraction of Japan's population is Taiwan's population as of 2025?",
        "Compare the main display specs of iPhone 15 and Samsung S24 (Resolution, Refresh Rate, Peak Brightness).",
        "Who is the CEO of the startup 'Morphic' AI search? (If there are multiple Morphic companies, focus on the AI search venture)."
    ]
    
    report_data = []
    
    for i, task in enumerate(tasks):
        print(f"\n{'='*20} Running Task {i+1} {'='*20}")
        answer, trace = agent.execute(task)
        
        task_record = {
            "task_id": i + 1,
            "query": task,
            "answer": answer,
            "trace": trace
        }
        report_data.append(task_record)
        
        # Save intermediate result
        with open(f"task_{i+1}_trace.txt", "w", encoding="utf-8") as f:
            f.write(trace)

    print("\nAll tasks completed. Traces saved to text files.")
    return report_data

if __name__ == "__main__":
    run_assignment()
