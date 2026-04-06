from database_builder_libs.stores.qdrant.qdrant_store import QdrantDatastore
from database_builder_libs.stores.typedb.typedb_store import TypeDbDatastore

from mcp_server.config import config

typedb = TypeDbDatastore()
typedb.connect(
        {
            "uri": config["typedb_uri"],
            "username": config["typedb_user"],
            "password": config["typedb_password"],
            "database": config["typedb_database"],
            "tls": config["typedb_uri"].startswith("https://")
        }
    )

qdrant = QdrantDatastore()
qdrant.connect(
    {
        "url": config["qdrant_url"],
        "collection": config["qdrant_collection"],
        "vector_size": config["qdrant_vector_size"],
        "api_key": config["qdrant_api_key"],
    }
)