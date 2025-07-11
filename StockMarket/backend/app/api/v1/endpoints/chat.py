from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import openai
from datetime import datetime

from app.core.config import settings
from app.db.session import get_db
from app.models.models import ChatMessage
from app.api.v1.endpoints.stocks import fetch_stock_data
from app.api.v1.endpoints.news import search_news

router = APIRouter()
openai.api_key = settings.OPENAI_API_KEY

SYSTEM_PROMPT = """You are a knowledgeable financial advisor AI. 
Use the provided context (stock data and news) to give accurate, informed advice.
Always consider both technical data and news sentiment in your analysis.
Be clear about uncertainties and risks in your recommendations."""

async def generate_context(query: str, db: Session) -> dict:
    """Generate context for the AI by fetching relevant stock data and news."""
    context = {
        "stock_data": [],
        "news_articles": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Extract stock symbols from query (simple approach)
    words = query.upper().split()
    potential_symbols = [word for word in words if word.isalpha() and len(word) <= 5]
    
    # Fetch stock data if symbols found
    for symbol in potential_symbols:
        try:
            stock_data = await fetch_stock_data(symbol)
            if stock_data:
                context["stock_data"].append(stock_data)
        except Exception:
            continue
    
    # Fetch relevant news
    try:
        news = await search_news(query, limit=3, db=db)
        context["news_articles"] = news
    except Exception:
        pass
    
    return context

async def generate_ai_response(query: str, context: dict) -> str:
    """Generate AI response using OpenAI API."""
    # Prepare context string
    context_str = "Current context:\n"
    
    if context["stock_data"]:
        context_str += "\nStock Data:\n"
        for stock in context["stock_data"]:
            context_str += f"- {stock['symbol']}: ${stock['price']} (Change: {stock['day_change']}%)\n"
    
    if context["news_articles"]:
        context_str += "\nRelevant News:\n"
        for article in context["news_articles"]:
            context_str += f"- {article['title']}\n"
            if article.get('content'):
                context_str += f"  Summary: {article['content'][:100]}...\n"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {query}"}
    ]
    
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@router.post("/ask")
async def ask_question(
    query: str,
    db: Session = Depends(get_db)
) -> dict:
    """Ask a question about stocks and get AI-powered response."""
    try:
        # Generate context
        context = await generate_context(query, db)
        
        # Generate AI response
        response = await generate_ai_response(query, context)
        
        # Store chat history
        chat_message = ChatMessage(
            user_id=1,  # Placeholder, replace with actual user_id from auth
            message=query,
            response=response,
            context_data=context
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        return {
            "response": response,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(
    db: Session = Depends(get_db),
    limit: Optional[int] = 10
) -> List[dict]:
    """Get user's chat history."""
    # Note: User authentication to be implemented
    history = db.query(ChatMessage).filter(
        ChatMessage.user_id == 1  # Placeholder, replace with actual user_id from auth
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": msg.id,
            "message": msg.message,
            "response": msg.response,
            "context": msg.context_data,
            "created_at": msg.created_at.isoformat()
        }
        for msg in history
    ] 