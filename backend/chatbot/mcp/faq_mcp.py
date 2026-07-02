from fastmcp import FastMCP

mcp = FastMCP("FAQMCP")

FAQ_DB = {
    "timings": "We are open from 10 AM to 11 PM every day.",
    "delivery": "Yes, we provide delivery within 5 km radius.",
    "payment": "We accept UPI, cash, and cards.",
    "veg": "Yes, we have a separate vegetarian kitchen section.",
    "reservation": "You can reserve tables via our chatbot."
}


@mcp.tool()
def ask_faq(question: str):
    """Answer restaurant FAQs"""

    q = question.lower()

    for key, answer in FAQ_DB.items():
        if key in q:
            return {"answer": answer}

    return {
        "answer": "Sorry, I don't have information about that. Please contact staff."
    }


@mcp.tool()
def list_faq():
    """List all FAQ topics"""

    return list(FAQ_DB.keys())


import os

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("FAQ_MCP_PORT", "8004"))
    )