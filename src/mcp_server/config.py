import os
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


config: dict = {
    "openai_host": require_env("OPENAI_HOST"),
    "openai_key": require_env("OPENAI_API_KEY"),
    "embedding_model": require_env("OPENAI_EMBEDDING_MODEL"),
    # TYPEDB
    "typedb_uri": require_env("TYPEDB_URI"),
    "typedb_database": require_env("TYPEDB_DATABASE"),
    # QDRANT
    "qdrant_url": require_env("QDRANT_URL"),
    "qdrant_collection": require_env("QDRANT_COLLECTION"),
    "qdrant_vector_size": require_env("QDRANT_VECTOR_SIZE"),
    # LANGFUSE
    "langfuse_secret_key": require_env("LANGFUSE_SECRET_KEY"),
    "langfuse_public_key": require_env("LANGFUSE_PUBLIC_KEY"),
    "langfuse_host": require_env("LANGFUSE_HOST"),
}
