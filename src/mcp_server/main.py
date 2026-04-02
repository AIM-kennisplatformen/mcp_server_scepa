from langfuse import observe
from mcp.server.fastmcp import FastMCP
from qdrant_client.models import FieldCondition, Filter, MatchAny

from database_builder_libs.stores.qdrant.qdrant_store import QdrantDatastore
from database_builder_libs.stores.typedb.typedb_store import TypeDbDatastore
from database_builder_libs.utility.embed_chunk.openai_compatible import (
    OpenAICompatibleChunkEmbedder,
)

from database_builder_libs.models.chunk import Chunk

from src.mcp_server.config import config
from src.mcp_server.sources.typedb_source import TypeDBSource

# -------------------------------
# MCP server initialization
# -------------------------------
mcp = FastMCP("paper_search")

typedb = TypeDbDatastore()
typedb.connect(
        {
            "uri": config["typedb_uri"],
            "username": "admin",
            "password": "password",
            "database": config["typedb_database"]
        }
    )
typedb_source = TypeDBSource(typedb)

qdrant = QdrantDatastore()
qdrant.connect(
    {
        "url": config["qdrant_url"],
        "collection": config["qdrant_collection"],
        "vector_size": config["qdrant_vector_size"],
    }
)


@mcp.tool()
@observe(name="get_literature_supported_knowledge_sources")
def get_literature_supported_knowledge(
    full_question: str, keywords_related_to_question: str
) -> str:
    """
    Provide a human-readable summary of relevant literature
    in which Zotero titles are linked to Qdrant results.
    """
    print(
        "tool_call, full_question: "
        + full_question
        + " keywords: "
        + keywords_related_to_question
    )

    # 1. Retrieve TypeDB metadata
    related_sources = typedb_source.extract_metadata(
        query=keywords_related_to_question
    )

    if not related_sources:
        return "No relevant literature was found based on the provided keywords."

    # 2. Collect Document keys (hashes)
    hashes = [s.get("key") for s in related_sources if "key" in s]
    if not hashes:
        return "No valid document references were found."

    # 3. Create lookup table: {hash -> title}
    title_lookup = {
        src["key"]: src["data"].get("title", "Unknown title")
        for src in related_sources
        if "key" in src and "data" in src
    }

    # 4. Query Qdrant
    query_chunk = Chunk(
        document_id="query", chunk_index=0, text=full_question, vector=(), metadata={}
    )
    embedding_chunks = OpenAICompatibleChunkEmbedder(
        base_url=config["openai_host"],
        api_key=config["openai_key"],
        model=config["embedding_model"],
    ).embed([query_chunk])

    query_vector = list(embedding_chunks[0].vector)

    valid_hashes = [str(h) for h in hashes if h is not None]
    filter = Filter(
        must=[
            FieldCondition(
                key="document_id",
                match=MatchAny(any=valid_hashes),
            )
        ]
    )

    response = qdrant._client().query_points(
        collection_name=qdrant._collection(),
        query=query_vector,
        limit=30,
        query_filter=filter,
        with_payload=True,
        with_vectors=False,
    )

    qdrant_results = [
        (point.payload or {}) | {"score": float(point.score)}
        for point in response.points
    ]

    if not qdrant_results:
        return "No relevant text fragments were found in the knowledge base."

    # 5. Build a clean summary
    lines = ["Relevant literature found:\n"]

    for item in qdrant_results:
        hash_key = item.get("document_id") or item.get("zotero_hash")
        title = title_lookup.get(hash_key, "Unknown title")
        score = item.get("score", 0)
        snippet = str(item.get("text", "")).strip()

        # Truncate snippet if too long
        if len(snippet) > 500:
            snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

        lines.append(f"— Score {score:.2f}\n  Title: {title}\n  Source: {snippet}\n")

    return "\n".join(lines)



if __name__ == "__main__":
    # mcp.settings.host="0.0.0.0"
    # mcp.settings.port=10000
    # mcp.run(transport="sse")
    get_literature_supported_knowledge("Agro puning", "Best practices")