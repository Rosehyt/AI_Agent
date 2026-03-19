import os
import re
import sys
import io
from openai import OpenAI
from dotenv import load_dotenv
from tools import search_tool

# Force UTF-8 encoding for stdout on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

class ReActAgent:
    def __init__(self, model="openai/gpt-4o-mini", max_iterations=8):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("MODEL_NAME", model)
        self.max_iterations = max_iterations
        self.system_prompt = """You are a highly capable AI assistant that uses a Reason-and-Act (ReAct) framework.
Your goal is to solve complex queries by interleaving reasoning (Thought) and actions (Action).

Available Tools:
- Search[query]: Searches the web for information using Tavily. Use this for population data, tech specs, or verifying identities.

Required Format:
Thought: A logical planning step where you reflect on what you know and what you need to find out.
Action: Search["query"]
Observation: [The system will provide this]
... (Repeat Thought -> Action -> Observation as needed)
Thought: I have sufficiently gathered and analyzed all information.
Final Answer: [A clear, direct, and comprehensive answer to the user's request]

Few-Shot Examples:

Example 1: Specificity & Calculation
User: "What is 15% of the population of France in 2024?"
Thought: I need to find the population of France in 2024 first.
Action: Search["France population 2024"]
Observation: "France's population is estimated at 68.3 million in 2024."
Thought: I have the population (68.3 million). Now I must calculate 15%. 68.3 * 0.15 = 10.245.
Final Answer: 15% of France's 2024 population is approximately 10.245 million.

Example 2: Reflection and Resilience
User: "Who is the CEO of BlueSky AI?"
Thought: I will search for the CEO of BlueSky AI.
Action: Search["BlueSky AI CEO"]
Observation: "BlueSky is a decentralized social network... Jay Graber is the CEO."
Thought: Wait, BlueSky social network is different from 'BlueSky AI' mentioned by the user. I should check if there is a specific 'BlueSky AI' startup or if the user meant something else.
Action: Search["BlueSky AI startup search engine CEO"]
Observation: "BlueSky AI, a new search venture, is led by John Doe."
Thought: I have found the correct specific entity.
Final Answer: The CEO of the startup BlueSky AI is John Doe.

IMPORTANT:
- Always start every iteration with a 'Thought'.
- Use 'Action: Search["query"]' precisely.
- STOP generating after the 'Action' line. Do NOT write your own Observation.
- If a search fails or is ambiguous, REFLECT on the results and try a more specific or different query.
- **Verification Rule**: If you find a named CEO/founder, you MUST verify in the observation that they are actually affiliated with the specific product requested (e.g., 'AI search'). If the observation shows they are from an unrelated field (e.g., Biotech, Healthcare, Blockchain/Polygon), you MUST REFLECT, state that this is the wrong entity, and search again using different keywords (e.g., add 'founders', 'YC', or specific product details).
- **Anti-Mismatch Rule**: Do NOT combine a product from one search result with a CEO from a different search result just because the company names are similar. The observation MUST explicitly link the person to the AI search project.
- **Entity Disambiguation Rule**: If you discover that the requested entity is an open-source project (e.g., morphic.sh) without a traditional CEO, your Final Answer MUST perform Entity Disambiguation: state clearly that it is an open-source project with no public CEO, and clarify that any commonly found CEOs (such as Jaynti Kanani) belong to DIFFERENT, unrelated companies.
- If you cannot find an exact 'CEO' after multiple searches, finding the 'founder' or 'creator' is sufficient for the Final Answer.
- **CRITICAL**: Your Final Answer MUST be written entirely in Traditional Chinese (繁體中文).
"""

    def execute(self, query):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        trace = []
        trace.append(f"--- Starting Task: {query} ---")
        print(f"\n--- Starting Task: {query} ---")
        
        for i in range(self.max_iterations):
            iter_msg = f"\n[Iteration {i+1}/{self.max_iterations}]"
            trace.append(iter_msg)
            print(iter_msg)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stop=["Observation:", "Observation"]
            )
            
            content = response.choices[0].message.content.strip()
            trace.append(content)
            print(content)
            
            # Check for Final Answer
            if "Final Answer:" in content:
                final_answer = content.split("Final Answer:")[1].strip()
                return final_answer, "\n".join(trace)
            
            # Match Action
            action_match = re.search(r"Action: (\w+)\[\"(.*)\"\]", content)
            
            if action_match:
                tool_name = action_match.group(1)
                tool_input = action_match.group(2)
                
                if tool_name == "Search":
                    obs_msg = f"\n[Calling Tool: {tool_name} with input: {tool_input}]"
                    print(obs_msg)
                    observation = search_tool(tool_input)
                else:
                    observation = f"Error: Tool {tool_name} not found."
                
                obs_out = f"Observation: {observation}"
                trace.append(obs_out)
                print(f"Observation: {observation[:200]}..." if len(observation) > 200 else f"Observation: {observation}")
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                # If LLM didn't format correctly, prompt it
                error_msg = "Please provide an 'Action: Search[\"query\"]' or a 'Final Answer:' using the required format."
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": error_msg})
                trace.append(f"System: {error_msg}")

        return "Error: Maximum iterations reached.", "\n".join(trace)

if __name__ == "__main__":
    agent = ReActAgent()
    # Test with a simple query if run directly
    result, trace = agent.execute("Who won the Super Bowl in 2024?")
    print(f"\nFinal Result: {result}")
