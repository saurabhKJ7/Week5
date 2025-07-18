from fastapi import APIRouter, Query
from typing import List
from app.agent.sql_agent import get_sql_agent

router = APIRouter()

@router.get("/prices/cheapest")
async def get_cheapest_price(item: str):
    """
    Finds which platform has the cheapest price for a given item.
    """
    agent = get_sql_agent()
    nl_query = f"Which app has the cheapest {item} right now?"
    result = agent.invoke({"input": nl_query})
    return {"response": result['output']}

@router.get("/discounts")
async def get_discounts(platform: str, min_pct: int = 30):
    """
    Shows products with a minimum percentage discount on a given platform.
    """
    agent = get_sql_agent()
    nl_query = f"Show products with {min_pct}%+ discount on {platform}"
    result = agent.invoke({"input": nl_query})
    return {"response": result['output']}

@router.get("/compare")
async def compare_prices(
    items: List[str] = Query(...),
    platforms: List[str] = Query(...)
):
    """
    Compares prices for a list of items between a list of platforms.
    """
    agent = get_sql_agent()
    items_str = ", ".join(items)
    platforms_str = " and ".join(platforms)
    nl_query = f"Compare {items_str} prices between {platforms_str}"
    result = agent.invoke({"input": nl_query})
    return {"response": result['output']} 