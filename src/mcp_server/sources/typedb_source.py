from typing import Any
from loguru import logger
from database_builder_libs.stores.typedb.typedb_store import TypeDbDatastore

class TypeDBSource:
    def __init__(self, typedb: TypeDbDatastore) -> None:
        self.typedb = typedb

    def extract_metadata(
self, query: str
    ) -> list[dict[str, Any]] | None:
        """Extract metadata for a document title
        
        Args:
            `query`: The keywords to search for in document titles
        
        Returns:
            List of dicts containing 'key' (hashvalue) and 'data' (with 'title')
        """
        logger.debug(f"Fetching metadata from TypeDB for documents (query: {query})")
        formatted = []
        relations = self.typedb.get_relations("relation=discriminatingconcept-bol")
        for relation in relations:
            logger.debug(f"rel: {relation}")
        return formatted

    @staticmethod
    def _extract_value(obj: Any) -> Any:
        """
        Extract the actual value from a TypeDB fetch result.
        
        TypeDB may return:
        - Raw values (strings, numbers) directly
        - Wrapped objects with a "value" key: {"value": ...}
        - None if the attribute is missing
        
        This method handles all cases safely.
        """
        if obj is None:
            return None
        
        # If it's a dictionary with a "value" key, extract it
        if isinstance(obj, dict):
            return obj.get("value")
        
        # Otherwise, return as-is (it's already a raw value)
        return obj