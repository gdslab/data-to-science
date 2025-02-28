from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.api import deps

extra_router = APIRouter()


@extra_router.get("/sl/{short_id}")
async def redirect_short_url(short_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Redirects to the original URL based on the provided short ID.
    """
    shortened_url = crud.shortened_url.get_by_short_id(db, short_id=short_id)
    if not shortened_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    original_url = shortened_url.original_url

    return RedirectResponse(
        url=original_url,
        status_code=303,
    )
