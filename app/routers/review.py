from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.models import Review, ReviewReply, User, Game as GameModel
from app.plugins.base import GameRegistry
from typing import List, Dict, Any, Optional

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_game_reviews(db: Session, game_slug: str) -> Dict[str, Any]:
    game = db.query(GameModel).filter(GameModel.slug == game_slug).first()
    if not game:
        return {"reviews": [], "average_rating": 0, "game_info": None}
    
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.game_id == game.id
    ).scalar() or 0
    
    reviews = db.query(
        Review,
        User.username,
    ).join(
        User, Review.user_id == User.id
    ).filter(
        Review.game_id == game.id
    ).order_by(desc(Review.created_at)).all()
    
    review_list = []
    for review, username in reviews:
        replies = db.query(
            ReviewReply,
            User.username.label("developer_name"),
        ).join(
            User, ReviewReply.developer_id == User.id
        ).filter(
            ReviewReply.review_id == review.id
        ).all()
        
        reply_list = [
            {
                "content": reply.content,
                "developer_name": dev_name,
                "created_at": reply.created_at,
            }
            for reply, dev_name in replies
        ]
        
        review_list.append({
            "id": review.id,
            "username": username,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at,
            "replies": reply_list,
        })
    
    return {
        "reviews": review_list,
        "average_rating": round(float(avg_rating), 1),
        "game_info": {
            "name": game.name,
            "slug": game.slug,
            "description": game.description,
        },
    }


@router.get("/{game_slug}", response_class=HTMLResponse)
async def reviews_page(
    request: Request,
    game_slug: str,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    
    game_plugin = GameRegistry.get(game_slug)
    if not game_plugin:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = db.query(GameModel).filter(GameModel.slug == game_slug).first()
    if not game:
        game = GameModel(
            name=game_plugin.name,
            slug=game_plugin.slug,
            description=game_plugin.description,
        )
        db.add(game)
        db.commit()
        db.refresh(game)
    
    review_data = get_game_reviews(db, game_slug)
    
    return templates.TemplateResponse(
        request,
        "reviews/index.html",
        {
            "user": user,
            "game_info": review_data["game_info"],
            "reviews": review_data["reviews"],
            "average_rating": review_data["average_rating"],
        },
    )


@router.post("/{game_slug}/submit")
async def submit_review(
    request: Request,
    game_slug: str,
    rating: int = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    game = db.query(GameModel).filter(GameModel.slug == game_slug).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    existing_review = db.query(Review).filter(
        Review.game_id == game.id,
        Review.user_id == user["user_id"],
    ).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
    else:
        new_review = Review(
            game_id=game.id,
            user_id=user["user_id"],
            rating=rating,
            comment=comment,
        )
        db.add(new_review)
    
    db.commit()
    
    return RedirectResponse(
        url=f"/reviews/{game_slug}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/reply/{review_id}")
async def submit_reply(
    request: Request,
    review_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    if not user.get("is_developer", False):
        raise HTTPException(
            status_code=403,
            detail="Only developers can reply to reviews",
        )
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    new_reply = ReviewReply(
        review_id=review_id,
        developer_id=user["user_id"],
        content=content,
    )
    db.add(new_reply)
    db.commit()
    
    game = db.query(GameModel).filter(GameModel.id == review.game_id).first()
    
    return RedirectResponse(
        url=f"/reviews/{game.slug}",
        status_code=status.HTTP_302_FOUND,
    )
