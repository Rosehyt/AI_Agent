import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Environment Setup
# ---------------------------------------------------------------------------
load_dotenv()

# Determine which API key to use (supports both OPENAI and GROQ environment names)
api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

if not api_key:
    # Fallback to checking the exact variable name in .env if needed
    print("Error: No API key found in .env (Looking for GROQ_API_KEY or OPENAI_API_KEY)")
    exit(1)

client = OpenAI(api_key=api_key, base_url=base_url)

# ---------------------------------------------------------------------------
# Mock Data Functions (Standardized)
# ---------------------------------------------------------------------------
EXCHANGE_RATES = {
    "USD_TWD": "32.0",
    "JPY_TWD": "0.2",
    "EUR_USD": "1.2",
}

STOCK_PRICES = {
    "AAPL": "260.00",
    "TSLA": "430.00",
    "NVDA": "190.00",
}


def get_exchange_rate(currency_pair: str) -> str:
    """Return the exchange rate for a given currency pair as a JSON string."""
    currency_pair = currency_pair.upper()
    rate = EXCHANGE_RATES.get(currency_pair)
    if rate is None:
        return json.dumps({"error": "Data not found"})
    return json.dumps({"currency_pair": currency_pair, "rate": rate})


def get_stock_price(symbol: str) -> str:
    """Return the stock price for a given symbol as a JSON string."""
    symbol = symbol.upper()
    price = STOCK_PRICES.get(symbol)
    if price is None:
        return json.dumps({"error": "Data not found"})
    return json.dumps({"symbol": symbol, "price": price})


# ---------------------------------------------------------------------------
# Function Map (Dictionary Dispatch)
# ---------------------------------------------------------------------------
available_functions = {
    "get_exchange_rate": get_exchange_rate,
    "get_stock_price": get_stock_price,
}

# ---------------------------------------------------------------------------
# Tool Schemas (Structured Outputs – strict: true)
# ---------------------------------------------------------------------------
# Requirement: "You must enable Structured Outputs by setting 'strict': true"
# and "Ensure all tool parameters include 'additionalProperties': false".
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate for a given currency pair (e.g. USD_TWD, JPY_TWD, EUR_USD).",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_pair": {
                        "type": "string",
                        "description": "The currency pair, e.g. 'USD_TWD'.",
                    }
                },
                "required": ["currency_pair"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the stock price for a given ticker symbol (e.g. AAPL, TSLA, NVDA).",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g. 'AAPL'.",
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
        },
    },
]

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful Financial Assistant. "
    "You can look up exchange rates and stock prices for the user. "
    "Always be polite and concise. If a tool returns an error, relay the "
    "information gracefully to the user without crashing. "
    "IMPORTANT: Only use the provided tools to fetch financial data. "
    "Respond in plain text without using special markup for function calls."
)

# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------

def run_agent():
    """Main loop: read user input, call LLM, handle tool calls, print reply."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 60)
    print(f"  Financial Assistant ({model_name})")
    print("  (type 'quit' or 'exit' to leave)")
    print("=" * 60)

    while True:
        # --- Get user input ------------------------------------------------
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # --- Call the LLM (may loop if there are tool calls) ---------------
        while True:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                )
            except Exception as e:
                # If tool_use_failed occurs (common with Groq + strict mode),
                # retry once without strict mode or with a cleaner prompt.
                print(f"\n[Error] API call failed: {e}")
                # Optional: For a real app, retry logic would go here.
                break

            assistant_message = response.choices[0].message

            # Append assistant message to history (standard dict format for compatibility)
            msg_to_append = {
                "role": "assistant",
                "content": assistant_message.content or "",
            }
            if assistant_message.tool_calls:
                msg_to_append["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ]
            
            messages.append(msg_to_append)

            # If there are NO tool calls, we have the final answer
            if not assistant_message.tool_calls:
                print(f"\nAssistant: {assistant_message.content}")
                break

            # --- Handle ALL tool calls (supports parallel calls) -----------
            print("\n[Debug] Tool calls in this turn:")
            for tool_call in assistant_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"  -> {func_name}({func_args})")

                # Dispatch via Function Map
                func_to_call = available_functions.get(func_name)
                if func_to_call:
                    result = func_to_call(**func_args)
                else:
                    result = json.dumps({"error": f"Unknown function: {func_name}"})

                # Append the tool result
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

            # Loop back to call the LLM again with the tool results


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_agent()
