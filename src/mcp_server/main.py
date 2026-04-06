from langfuse import observe
from fastmcp import FastMCP

from mcp_server.tools.paper_search import Keywords, LiteratureType, get_literature_supported_knowledge

# -------------------------------
# MCP server initialization
# -------------------------------
mcp = FastMCP("paper_search")

mcp.add_tool(get_literature_supported_knowledge)

if __name__ == "__main__":
    # mcp.run(
    #     transport="http", 
    #     host="0.0.0.0",
    #     port=8001
    # )
    print(get_literature_supported_knowledge("What are best practices for energy poverty?", [Keywords.BEST_PRACTICES], [LiteratureType.SCIENTIFIC]))