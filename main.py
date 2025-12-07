# main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, ForeignKey
)
from sqlalchemy.orm import (
    sessionmaker, declarative_base, relationship, Session, joinedload
)

# ============================================================
# Database setup (SQLite for simplicity; swap to Postgres/MySQL later)
# ============================================================
DATABASE_URL = "sqlite:///./blog.db"  # change to postgresql://... for Postgres

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# SQLAlchemy Models
# ============================================================
class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)

    # Cascade delete ensures posts are removed when author is deleted
    posts = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    author_id = Column(
        Integer,
        ForeignKey("authors.id", ondelete="CASCADE"),
        nullable=False
    )

    author = relationship("Author", back_populates="posts")


# Create tables
Base.metadata.create_all(bind=engine)


# ============================================================
# Pydantic Schemas (Request / Response models)
# ============================================================
class AuthorBase(BaseModel):
    name: str
    email: EmailStr


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class AuthorOut(AuthorBase):
    id: int

    class Config:
        orm_mode = True


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    author_id: int


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class PostOut(PostBase):
    id: int
    author_id: int
    author: Optional[AuthorOut] = None  # nested author details

    class Config:
        orm_mode = True


# ============================================================
# FastAPI app
# ============================================================
app = FastAPI(title="Blog API - Authors & Posts")


# ============================================================
# Author Endpoints (/authors)
# ============================================================
@app.post("/authors", response_model=AuthorOut)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    # Check for unique email
    existing = db.query(Author).filter(Author.email == author.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    new_author = Author(name=author.name, email=author.email)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author


@app.get("/authors", response_model=List[AuthorOut])
def list_authors(db: Session = Depends(get_db)):
    return db.query(Author).all()


@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.put("/authors/{author_id}", response_model=AuthorOut)
def update_author(author_id: int, data: AuthorUpdate, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    if data.name is not None:
        author.name = data.name
    if data.email is not None:
        # Optional: check if new email is unique
        email_owner = db.query(Author).filter(
            Author.email == data.email,
            Author.id != author_id
        ).first()
        if email_owner:
            raise HTTPException(status_code=400, detail="Email already in use")
        author.email = data.email

    db.commit()
    db.refresh(author)
    return author


@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    db.delete(author)
    db.commit()  # posts are deleted because of cascade
    return {"message": "Author and their posts deleted successfully"}


# ============================================================
# Post Endpoints (/posts)
# ============================================================
@app.post("/posts", response_model=PostOut)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    # Validate author existence (400-level error)
    author = db.query(Author).filter(Author.id == post.author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="Author does not exist")

    new_post = Post(
        title=post.title,
        content=post.content,
        author_id=post.author_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    # Eager load author for response
    db.refresh(new_post)
    return new_post


@app.get("/posts", response_model=List[PostOut])
def list_posts(
    author_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    GET /posts
    Optional filter: ?author_id=123
    Uses joinedload to avoid N+1 problem by eager loading authors.
    """
    query = db.query(Post).options(joinedload(Post.author))

    if author_id is not None:
        query = query.filter(Post.author_id == author_id)

    posts = query.all()
    return posts


@app.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    GET /posts/{id} - must return post data + nested author info.
    We use joinedload to fetch author in same query (efficient).
    """
    post = (
        db.query(Post)
        .options(joinedload(Post.author))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if data.title is not None:
        post.title = data.title
    if data.content is not None:
        post.content = data.content

    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}


# ============================================================
# Nested resource: GET /authors/{id}/posts
# ============================================================
@app.get("/authors/{author_id}/posts", response_model=List[PostOut])
def get_author_posts(author_id: int, db: Session = Depends(get_db)):
    # Optional: check author exists → return 404 if not
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    posts = (
        db.query(Post)
        .options(joinedload(Post.author))
        .filter(Post.author_id == author_id)
        .all()
    )
    return posts
