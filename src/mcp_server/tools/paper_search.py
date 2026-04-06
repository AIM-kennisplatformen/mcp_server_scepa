from enum import Enum

from langfuse import observe
from qdrant_client.models import FieldCondition, Filter, MatchAny
from database_builder_libs.utility.embed_chunk.openai_compatible import (
    OpenAICompatibleChunkEmbedder,
)
from database_builder_libs.models.chunk import Chunk

from mcp_server.utility.globals import typedb, qdrant
from mcp_server.config import config

class Keywords(Enum):
    BEST_PRACTICES = "best-practices"
    TARGET_GROUPS = "target-groups"
    STRATEGIC_OVERVIEW = "strategic-overview"

class LiteratureType(Enum):
    SCIENTIFIC = "scientific"
    PROJECT_REPORTS = "projectreports"
    SURVEYS = "surveys"
    GREY_LITERATURE = "greyliterature"

@observe(name="get_literature_supported_knowledge_sources")
def get_literature_supported_knowledge(
    full_question: str, 
    keywords_related_to_question: list[Keywords],
    literature_types: list[LiteratureType] | None = None
) -> str:
    """
    Retrieves relevant literature snippets from the knowledge base to answer a user's question.

    This tool filters the available literature based on specific strategic keywords and document types, 
    and then performs a semantic vector search to find the most contextually relevant text fragments.

    Args:
        full_question (str): The complete user query used to find semantically matching text.
        keywords_related_to_question (list[Keywords]): A list of strategic keywords to narrow 
            the search space to relevant domains.
        literature_types (list[LiteratureType] | None, optional): Specific document types 
            to restrict the search (e.g., scientific, surveys). Defaults to None.

    Returns:
        str: A formatted string containing the most relevant text fragments, along 
        with their source titles and relevance scores. Returns a fallback message if 
        no matches are found.
    """
    if literature_types is None:
        literature_types = []

    match_segments = ["$e isa textdocument;"]
    fetch_segments = ["'entity': { $e.* }"]

    if literature_types:
        lit_patterns = []
        for lit in literature_types:
            lit_val = lit.value
            lit_patterns.append(f"{{ ${lit_val} isa discriminatingconcept-bol-{lit_val} (attributedthing: $e); }}")
            fetch_segments.append(f"'{lit_val}': {{ ${lit_val}.* }}")
        
        match_segments.append(f"{' or '.join(lit_patterns)};")

    if keywords_related_to_question:
        func_patterns = []
        for func in keywords_related_to_question:
            func_patterns.append(f"{{ $bol isa discriminatingconcept-bol-scientific (attributedthing: $e), has function == '{func.value}'; }}")
        
        match_segments.append(f"{' or '.join(func_patterns)};")
        fetch_segments.append("'bol': { $bol.* }")

    query = f"""
        match
        {' '.join(match_segments)}
        fetch {{
            {', '.join(fetch_segments)}
        }};
    """

    related_sources = typedb.query_read(query=query).as_concept_documents()

    if not related_sources:
        return "No relevant literature was found based on the provided keywords."

    hashes = [
        source.get("entity").get("hashvalue") 
        for source in related_sources
    ]
    
    if not hashes:
        return "No valid document references were found."
    
    title_lookup = {
        src["key"]: src["data"].get("title", "Unknown title")
        for src in related_sources
        if "key" in src and "data" in src
    }

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
                key="document_hash",
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

    lines = ["Relevant literature found:\n"]

    for item in qdrant_results:
        hash_key = item.get("document_id") or item.get("zotero_hash")
        title = title_lookup.get(hash_key, "Unknown title")
        score = item.get("score", 0)
        snippet = str(item.get("text", "")).strip()

        # Truncate snippet if too long
        if len(snippet) > 500:
            snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

        lines.append(f"- Score {score:.2f}\n  Title: {title}\n  Source: {snippet}\n")

    return "\n".join(lines)
