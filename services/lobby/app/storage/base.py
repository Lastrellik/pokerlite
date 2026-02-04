"""Abstract storage interface for table management."""
from abc import ABC, abstractmethod
from typing import List, Optional
from models.table_config import TableConfig


class TableStorage(ABC):
    """Abstract interface for table storage."""

    @abstractmethod
    async def create_table(self, config: TableConfig) -> TableConfig:
        """Create a new table."""
        pass

    @abstractmethod
    async def get_table(self, table_id: str) -> Optional[TableConfig]:
        """Get a table by ID."""
        pass

    @abstractmethod
    async def list_tables(self) -> List[TableConfig]:
        """List all tables."""
        pass

    @abstractmethod
    async def delete_table(self, table_id: str) -> bool:
        """Delete a table. Returns True if deleted, False if not found."""
        pass
