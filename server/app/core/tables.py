from typing import Dict
from .models import TableState

_tables: Dict[str, TableState] = {}

def get_table(table_id: str) -> TableState:
    if table_id not in _tables:
        _tables[table_id] = TableState(table_id=table_id)
    return _tables[table_id]
