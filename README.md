# SCEPA-MCP

SCEPA MCP Server, serving as an MCP server for the SCEPA Knowledge Platform.

## Development

This project uses [pixi](https://prefix.dev) for dependency management:

```bash
pixi install
pixi run test
pixi run mcp_server
```

## MCP Tool Documentation

When documenting MCP tools (functions exposed to the LLM), **do not use standard Python docstrings for documentation**. The MCP protocol parses these docstrings to generate tool descriptions for the LLM. Using them for documentation can confuse the LLM and consume unnecessary tokens.

Instead, provide documentation using standard Python inline comments (`#`) directly within the code.

## License

See [LICENSE](LICENSE) for details.
