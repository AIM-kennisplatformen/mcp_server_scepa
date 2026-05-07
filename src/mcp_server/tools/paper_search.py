from enum import Enum
from pydantic import BaseModel, Field
from langfuse import observe
from qdrant_client.models import FieldCondition, Filter, MatchAny
from database_builder_libs.utility.embed_chunk.openai_compatible import (
    OpenAICompatibleChunkEmbedder,
)
from database_builder_libs.models.chunk import Chunk

from mcp_server.utility.globals import typedb, qdrant
from mcp_server.config import config

from sentence_transformers import CrossEncoder

class Keywords(str, Enum):
    BEST_PRACTICES = "best-practices"
    TARGET_GROUPS = "target-groups"
    STRATEGIC_OVERVIEW = "strategic-overview"

class LiteratureType(str, Enum):
    SCIENTIFIC = "scientific"
    PROJECT_REPORTS = "projectreports"
    SURVEYS = "surveys"
    GREY_LITERATURE = "greyliterature"

_reranker = CrossEncoder(
    config.get("reranker_model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
)

@observe(name="get_literature_supported_knowledge_sources")
def get_literature_supported_knowledge(
    full_question: str,
    keywords_related_to_question: list[Keywords],
    literature_types: list[LiteratureType] | None = None,
    # NEW: expose reranking knobs so callers can tune without touching internals
    rerank_top_k: int = 30,
) -> str:
    """
    Retrieves relevant literature snippets from the knowledge base to answer a user's question.

    This tool filters the available literature based on specific strategic keywords and document
    types, performs a semantic vector search to find the most contextually relevant text
    fragments, and then reranks the candidates with a cross-encoder for higher precision.

    Args:
        full_question (str): The complete user query used to find semantically matching text.
        keywords_related_to_question (list[Keywords]): A list of strategic keywords to narrow
            the search space to relevant domains.
            Valid values: 'best-practices', 'target-groups', 'strategic-overview'
        literature_types (list[LiteratureType] | None, optional): Specific document types
            to restrict the search. Valid values: null
        rerank_top_k (int): How many results to keep after reranking (default: 10).

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
            lit_patterns.append(
                f"{{ ${lit_val} isa discriminatingconcept-bol-{lit_val} "
                f"(attributedthing: $e); }}"
            )
            fetch_segments.append(f"'{lit_val}': {{ ${lit_val}.* }}")

        match_segments.append(f"{' or '.join(lit_patterns)};")

    if keywords_related_to_question:
        func_patterns = []
        for func in keywords_related_to_question:
            func_patterns.append(
                f"{{ $bol isa discriminatingconcept-bol-scientific "
                f"(attributedthing: $e), has function == '{func.value}'; }}"
            )

        match_segments.append(f"{' or '.join(func_patterns)};")
        fetch_segments.append("'bol': { $bol.* }")

    query = f"""
        match
        {' '.join(match_segments)}
        fetch {{
            {', '.join(fetch_segments)}
        }};
    """

    related_sources = list(typedb.query_read(query=query).as_concept_documents())

    if not related_sources:
        return "No relevant literature was found based on the provided keywords."

    hashes = [source["entity"]["hashvalue"] for source in related_sources]

    if not hashes:
        return "No valid document references were found."

    title_lookup = {
        source["entity"]["hashvalue"]: source["entity"]["namelike-title"]
        for source in related_sources
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

    # Retrieve extra candidates (3× rerank_top_k) so the reranker has
    # enough material to work with while we still return rerank_top_k.
    retrieval_limit = max(30, rerank_top_k * 3)

    valid_hashes = [str(h) for h in hashes if h is not None]
    qdrant_filter = Filter(
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
        limit=retrieval_limit,
        query_filter=qdrant_filter,
        with_payload=True,
        with_vectors=False,
    )

    qdrant_results = [
        (point.payload or {}) | {"vector_score": float(point.score)}
        for point in response.points
    ]

    if not qdrant_results:
        return "No relevant text fragments were found in the knowledge base."


    snippets = [str(item.get("text", "")).strip() for item in qdrant_results]

    # Cross-encoder expects (query, passage) pairs
    pairs = [(full_question, snippet) for snippet in snippets]
    rerank_scores = _reranker.predict(pairs)          # returns a numpy array

    # Attach rerank scores and sort descending
    for item, rerank_score in zip(qdrant_results, rerank_scores):
        item["rerank_score"] = float(rerank_score)

    reranked = sorted(qdrant_results, key=lambda x: x["rerank_score"], reverse=True)
    top_results = reranked[:rerank_top_k]

    lines = []

    for item in top_results:
        hash_key = item.get("document_hash")
        title = title_lookup.get(hash_key, "Unknown title")
        snippet = str(item.get("text", "")).strip()

        if len(snippet) > 500:
            snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

        lines.append(
            f"  Title: {title}\n"
            f"  Source: {snippet}\n"
        )

    return "\n".join(lines)