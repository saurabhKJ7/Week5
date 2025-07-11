from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import asyncio
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import get_db
from app.models.models import StockPrice, WatchlistItem
from app.core.websocket_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

async def fetch_stock_data(symbol: str) -> dict:
    """Fetch real-time stock data from StockData.org API."""
    url = f"https://api.stockdata.org/v1/data/quote"
    params = {
        "symbols": symbol,
        "api_token": settings.STOCKDATA_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch stock data")
        
        data = response.json()
        return data["data"][0] if data.get("data") else None

@router.get("/live/{symbol}")
async def get_live_stock_data(
    symbol: str,
    db: Session = Depends(get_db)
) -> dict:
    """Get real-time stock data for a specific symbol."""
    try:
        stock_data = await fetch_stock_data(symbol)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        # Store the price data
        price = StockPrice(
            symbol=symbol,
            price=stock_data["price"],
            volume=stock_data["volume"],
            timestamp=datetime.utcnow()
        )
        db.add(price)
        db.commit()
        
        return stock_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}")
async def get_stock_history(
    symbol: str,
    days: Optional[int] = 7,
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get historical stock data for a specific symbol."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    prices = db.query(StockPrice).filter(
        StockPrice.symbol == symbol,
        StockPrice.timestamp >= cutoff_date
    ).order_by(StockPrice.timestamp.desc()).all()
    
    return [
        {
            "price": price.price,
            "volume": price.volume,
            "timestamp": price.timestamp.isoformat()
        }
        for price in prices
    ]

@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
) -> dict:
    """Add a stock to user's watchlist."""
    # Note: User authentication to be implemented
    watchlist_item = WatchlistItem(
        user_id=1,  # Placeholder, replace with actual user_id from auth
        symbol=symbol,
        notes=notes
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    
    return {"message": f"Added {symbol} to watchlist", "id": watchlist_item.id}

@router.get("/watchlist")
async def get_watchlist(
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get user's watchlist with current prices."""
    # Note: User authentication to be implemented
    watchlist = db.query(WatchlistItem).filter(WatchlistItem.user_id == 1).all()
    
    result = []
    for item in watchlist:
        try:
            stock_data = await fetch_stock_data(item.symbol)
            result.append({
                "id": item.id,
                "symbol": item.symbol,
                "notes": item.notes,
                "current_price": stock_data["price"] if stock_data else None,
                "price_change": stock_data["day_change"] if stock_data else None
            })
        except Exception:
            # If we can't fetch current price, still return the watchlist item
            result.append({
                "id": item.id,
                "symbol": item.symbol,
                "notes": item.notes,
                "current_price": None,
                "price_change": None
            })
    
    return result

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db)
) -> dict:
    """Remove a stock from user's watchlist."""
    # Note: User authentication to be implemented
    db.query(WatchlistItem).filter(
        WatchlistItem.user_id == 1,
        WatchlistItem.symbol == symbol
    ).delete()
    db.commit()
    
    return {"message": f"Removed {symbol} from watchlist"} 