# **Studio App**

This repository contains the tools for the MCP Server for the SCEPA studio application.

All components run locally within a **Pixi environment**.
No LibreChat or Docker-based workflow is required for development.

---

# 🚀 Features

* Modular architecture with isolated components
* Zotero + Qdrant vector search
* Optional telemetry (Langfuse)

---

# 🖥️ System Requirements

## Development Requirements

* Linux, macOS, or Windows
* Intel/AMD x86_64 or ARM 64-bit
* **Pixi** installed → [https://pixi.sh/latest/installation/](https://pixi.sh/latest/installation/)


---

# 📁 Project Structure

```
src/
  mcp_server/     # MCP server implementation
```

---

# 🔧 Configuration Files

Two configuration files must be created before the system can run:

### 1. `.env`

```
cp .env.sample .env
```

---

# 📑 Environment Variables (`.env`)

Below is the full explanation of every field included in `.env.sample`.

---

## TypeDB Graph Database

Used for querying graph data.

```
TYPEDB_URI="127.0.0.1:1739"
TYPEDB_DATABASE="scepa"
```

---

## 📚 Zotero (MCP Paper Search)

Used only if the MCP server needs to query academic papers.

```
ZOTERO_API_KEY=""
ZOTERO_LIBRARY_ID=""
ZOTERO_COLLECTION_ID=""
```

### Where to find them:

* **API key** → Zotero settings → Feeds/API
* **Library ID** → URL:
  `https://www.zotero.org/groups/<library_id>/<name>/library`
* **Collection ID** → URL:
  `https://.../collections/<collection_id>/collection`

---

## 🗂️ Qdrant Vector Database

Used for document embeddings / semantic search.

```
QDRANT_URL="http://127.0.0.1"
QDRANT_PORT=6333
```

Defaults are correct for local Qdrant.

---

## 📊 Optional — Langfuse Telemetry

If you want tracing / prompt analytics:

```
LANGFUSE_SECRET_KEY=""
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_HOST=""
```

