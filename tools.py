import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

def search_tool(query: str) -> str:
    """
    Search the web using Tavily API.
    Returns a clean string representation of the results.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment."
    
    try:
        tavily = TavilyClient(api_key=api_key)
        response = tavily.search(query=query, search_depth="advanced", max_results=3)
        
        results = []
        for result in response.get("results", []):
            results.append(f"Title: {result.get('title')}\nContent: {result.get('content')}\nURL: {result.get('url')}")
        
        return "\n\n".join(results) if results else "No relevant results found."
    
    except Exception as e:
        return f"Error during search: {str(e)}"

if __name__ == "__main__":
    print(search_tool("Japan population 2025"))
