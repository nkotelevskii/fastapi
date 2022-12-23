from typing import Optional

from fastapi import status, HTTPException, Response, Depends, APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas, database, oauth2

router = APIRouter(prefix="/posts", tags=["Posts"])


# @router.get("/", response_model=list[schemas.Post])
@router.get("/", response_model=list[schemas.PostOut])
def get_posts(db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user), limit: int = 10,
              skip: int = 0, search: Optional[str] = ""):
    # posts = db.query(models.Post).filter(models.Post.title.contains(search)).offset(skip).limit(limit).all()

    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote,
                                                                                       models.Vote.post_id == models.Post.id,
                                                                                       isouter=True).group_by(
        models.Post.id).filter(models.Post.title.contains(search)).offset(skip).limit(limit).all()

    return posts


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate, db: Session = Depends(database.get_db),
                 current_user=Depends(oauth2.get_current_user)):
    new_post = models.Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)  # local changes
    db.commit()  # push changes to a database
    db.refresh(new_post)  # inplace correction -- fills fields like TIMESTAMP, ID etc.
    return new_post


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user)):
    selected_post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(models.Vote,
                                                                                               models.Vote.post_id == models.Post.id,
                                                                                               isouter=True).group_by(
        models.Post.id).filter(models.Post.id == post_id).first()
    if selected_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")
    return selected_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(database.get_db), current_user=Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")

    if current_user.id != post.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform requested section!")
    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{post_id}", status_code=status.HTTP_205_RESET_CONTENT, response_model=schemas.Post)
def update_post(post_id: int, updated_post: schemas.PostCreate, db: Session = Depends(database.get_db),
                current_user=Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")
    if current_user.id != post.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform requested section!")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()
