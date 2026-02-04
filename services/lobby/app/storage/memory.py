"""In-memory table storage implementation."""
from typing import Dict, List, Optional
from .base import TableStorage
from models.table_config import TableConfig


class InMemoryTableStorage(TableStorage):
    """In-memory implementation of table storage."""

    def __init__(self):
        self._tables: Dict[str, TableConfig] = {}

    async def create_table(self, config: TableConfig) -> TableConfig:
        """Create a new table."""
        self._tables[config.table_id] = config
        return config

    async def get_table(self, table_id: str) -> Optional[TableConfig]:
        """Get a table by ID."""
        return self._tables.get(table_id)

    async def list_tables(self) -> List[TableConfig]:
        """List all tables."""
        return list(self._tables.values())

    async def delete_table(self, table_id: str) -> bool:
        """Delete a table."""
        if table_id in self._tables:
            del self._tables[table_id]
            return True
        return False
