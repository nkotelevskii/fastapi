import time
from typing import Optional

import psycopg2
from fastapi import FastAPI, status, HTTPException, Response
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from .AUTH import USERNAME, PASSWORD, HOST, DATABASE

app = FastAPI()

while True:
    try:
        conn = psycopg2.connect(host=HOST,
                                database=DATABASE,
                                user=USERNAME,
                                password=PASSWORD,
                                cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Database connection was successful!")
        break
    except Exception as error:
        print("Connection to the database failed!")
        print(f"The error was: {error}")
        time.sleep(2)


class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


@app.get("/")
async def root():
    return {"message": "Hello World!!"}


@app.get("/posts")
async def get_posts():
    cursor.execute(
        """
        SELECT * FROM posts
        """
    )
    posts = cursor.fetchall()
    return {"data": posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_posts(post: Post):
    cursor.execute(
        """
        INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *
        """, (post.title, post.content, post.published)
    )
    new_post = cursor.fetchone()
    conn.commit()
    return {"data": new_post}


@app.get("/posts/{post_id}")
def get_post(post_id: int):
    cursor.execute(
        """
        SELECT * FROM posts WHERE id = %s
        """, (str(post_id))
    )
    selected_post = cursor.fetchone()
    if selected_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")
    return {"post_details": selected_post}


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int):
    cursor.execute(
        """
        DELETE FROM posts WHERE id=%s RETURNING *
        """, (str(post_id))
    )
    selected_post = cursor.fetchone()
    conn.commit()
    if selected_post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{post_id}", status_code=status.HTTP_205_RESET_CONTENT)
def update_post(post_id: int, post: Post):
    cursor.execute(
        """
        UPDATE posts SET title = %s, content=%s, published=%s WHERE id=%s RETURNING *
        """, (post.title, post.content, post.published, post_id)
    )
    post_updated = cursor.fetchone()
    conn.commit()
    if post_updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"A post with id {post_id} was not found!")
    return {"message": post_updated}
