from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from mcp_server.tools.paper_search import get_literature_supported_knowledge

# -------------------------------
# MCP server initialization
# -------------------------------
mcp = FastMCP("paper_search")

mcp.add_tool(get_literature_supported_knowledge)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
