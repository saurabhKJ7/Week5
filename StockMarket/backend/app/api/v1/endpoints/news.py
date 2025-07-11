from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
from datetime import datetime, timedelta
import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.db.session import get_db
from app.models.models import NewsArticle

router = APIRouter()

# Initialize ChromaDB and sentence transformer
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
news_collection = chroma_client.get_or_create_collection(name="financial_news")
sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')

async def fetch_news_from_api(query: str = "stock market") -> List[dict]:
    """Fetch news from NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": settings.NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch news")
        
        return response.json()["articles"]

@router.get("/trending")
async def get_trending_news(
    db: Session = Depends(get_db),
    query: Optional[str] = "stock market",
    limit: Optional[int] = 10
) -> List[dict]:
    """Get trending financial news."""
    try:
        articles = await fetch_news_from_api(query)
        
        # Process and store articles
        stored_articles = []
        for article in articles[:limit]:
            # Create embedding for the article
            text_to_embed = f"{article['title']} {article['description']}"
            embedding = sentence_transformer.encode(text_to_embed).tolist()
            
            # Store in database
            db_article = NewsArticle(
                title=article["title"],
                content=article.get("description", ""),
                url=article["url"],
                source=article["source"]["name"],
                published_at=datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00")),
                embedding=embedding
            )
            db.add(db_article)
            
            # Store in vector database
            news_collection.add(
                documents=[text_to_embed],
                metadatas=[{"url": article["url"], "source": article["source"]["name"]}],
                ids=[str(hash(article["url"]))],
                embeddings=[embedding]
            )
            
            stored_articles.append({
                "title": article["title"],
                "description": article.get("description", ""),
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"]
            })
        
        db.commit()
        return stored_articles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_news(
    query: str,
    limit: Optional[int] = 5,
    db: Session = Depends(get_db)
) -> List[dict]:
    """Search news articles using semantic search."""
    try:
        # Create query embedding
        query_embedding = sentence_transformer.encode(query).tolist()
        
        # Search in vector database
        results = news_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        # Get full articles from database
        articles = []
        for i, url in enumerate(results["metadatas"][0]["url"]):
            article = db.query(NewsArticle).filter(NewsArticle.url == url).first()
            if article:
                articles.append({
                    "title": article.title,
                    "content": article.content,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at.isoformat(),
                    "relevance_score": results["distances"][0][i]
                })
        
        return articles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{symbol}")
async def get_stock_news(
    symbol: str,
    days: Optional[int] = 7,
    limit: Optional[int] = 5
) -> List[dict]:
    """Get news specific to a stock symbol."""
    try:
        articles = await fetch_news_from_api(f"{symbol} stock")
        return articles[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 