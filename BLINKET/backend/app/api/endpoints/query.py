import logging
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.db.sync_session import SyncSessionLocal  # Use sync session
from app.db.base import Base

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str

# ------------------------------------------------------------
# Generic FK-ID → human label mapper
# ------------------------------------------------------------
_ID_PATTERN = re.compile(r"(\w+)_id\s+(\d+)")
# Build a mapping from prefix (e.g. 'platform') → (table_name, label_column)
_PREFIX_TO_TABLE: dict[str, tuple[str, str]] = {}
for mapper in Base.registry.mappers:  # iterate all SQLAlchemy models
    table = mapper.persist_selectable  # Table object
    cols = table.c.keys()
    # Determine a human label column to fetch
    label_col = None
    for candidate in ("name", "code", "title", "description"):
        if candidate in cols:
            label_col = candidate
            break
    if label_col:
        prefix = table.name.rstrip("s")  # crude plural → singular
        _PREFIX_TO_TABLE[prefix] = (table.name, label_col)


def _humanize(response: str) -> str:
    """Replace `<prefix>_id N` tokens with their human-readable value."""
    pairs = _ID_PATTERN.findall(response)
    if not pairs:
        return response
    with SyncSessionLocal() as session:  # Use sync session
        for prefix, id_ in set(pairs):
            mapping = _PREFIX_TO_TABLE.get(prefix)
            if not mapping:
                continue
            table, label_col = mapping
            sql = text(f"SELECT {label_col} FROM {table} WHERE id = :id")
            label = session.execute(sql, {"id": id_}).scalar()
            if label:
                response = response.replace(f"{prefix}_id {id_}", str(label))
    return response

# ------------------------------------------------------------

@router.post("/nl-query")
async def query(request: QueryRequest):
    if request.query == "health-check":
        return {"response": "ok"}

    from app.agent.sql_agent import get_sql_agent  # deferred import

    try:
        agent = get_sql_agent()
        result = agent.invoke({"input": request.query})
        output = result["output"]
        output = _humanize(output)
        return {"response": output}
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 