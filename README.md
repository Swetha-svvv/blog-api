# Blog API – Authors & Posts

A simple RESTful API for a blog platform that manages **authors** and their **posts**, built using **FastAPI**, **SQLAlchemy**, and **SQLite**.

This project demonstrates:

* One-to-many relationship (**Author → Posts**)
* Foreign key constraints with **Cascade Delete**
* Validation (no posts for non-existent authors)
* Efficient query handling using `joinedload` (prevents N+1 problem)
* Full CRUD for Authors & Posts
* Clean & well-structured API architecture

---

## 🚀 Tech Stack

| Component  | Technology   |
| ---------- | ------------ |
| Language   | Python 3.11+ |
| Framework  | FastAPI      |
| ORM        | SQLAlchemy   |
| Database   | SQLite       |
| Server     | Uvicorn      |
| Validation | Pydantic     |

---

## ⚙ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/blog-api.git
cd blog-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
uvicorn main:app --reload
```

---

### URLs:

| Feature      | URL                                                        |
| ------------ | ---------------------------------------------------------- |
| Base URL     | [http://127.0.0.1:8000](http://127.0.0.1:8000)             |
| Swagger Docs | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)   |
| ReDoc Docs   | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |

---

## 🗄 Database Schema

### Tables

**Authors**

```
id (PK)
name
email (unique)
```

**Posts**

```
id (PK)
title
content
author_id (FK -> authors.id, On Delete Cascade)
```

### ER Diagram

```
+-----------------+         1       ∞        +-----------------+
|    authors      |------------------------>|      posts      |
+-----------------+                         +-----------------+
| id (PK)         |                         | id (PK)         |
| name            |                         | title           |
| email (UNIQUE)  |                         | content         |
+-----------------+                         | author_id (FK)  |
                                            +-----------------+
```

> When an author is deleted, all their posts are automatically removed due to cascade delete.

---

## 📌 API Endpoints Summary

### Authors – `/authors`

| Method | Endpoint              | Description                   |
| ------ | --------------------- | ----------------------------- |
| POST   | `/authors`            | Create Author                 |
| GET    | `/authors`            | List all Authors              |
| GET    | `/authors/{id}`       | Get Author by ID              |
| PUT    | `/authors/{id}`       | Update Author                 |
| DELETE | `/authors/{id}`       | Delete Author (Cascade Posts) |
| GET    | `/authors/{id}/posts` | List posts of an author       |

#### Example

```json
{
  "name": "Swetha",
  "email": "siripurapuswetha06@gmail.com"
}
```

---

### Posts – `/posts`

| Method | Endpoint      | Description                         |
| ------ | ------------- | ----------------------------------- |
| POST   | `/posts`      | Create Post                         |
| GET    | `/posts`      | List Posts (+ filter `?author_id=`) |
| GET    | `/posts/{id}` | Get single post with author         |
| PUT    | `/posts/{id}` | Update post                         |
| DELETE | `/posts/{id}` | Delete post                         |

#### Create Post Example

```json
{
  "title": "My First Blog Post",
  "content": "Hello from my API!",
  "author_id": 1
}
```

#### Filter

```
GET /posts?author_id=1
```

#### Response

```json
[
  {
    "id": 1,
    "title": "My First Blog Post",
    "content": "Hello from my API!",
    "author_id": 1,
    "author": {
      "id": 1,
      "name": "Swetha",
      "email": "siripurapuswetha06@gmail.com"
    }
  }
]

