# Backend

ATLAS backend api.

## TODO

* search and order by
* pytest

## Libraries

* [FastAPI](https://fastapi.tiangolo.com)
* [SQLModel](https://sqlmodel.tiangolo.com)
* [Pydantic](https://docs.pydantic.dev/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [Alembic](https://alembic.sqlalchemy.org/en/latest/)

## Models

```dbml
Table item {
  id "int identity" [primary key]
  title varchar
  item_type item_type
  collection_id int [ref: > collection.id]
  stack_id int [ref: > stack.id]
  shelf int
  slot int
  annotations jsonb
}

enum item_type {
  "Book"
  "Magazine"
  "Illustration"
  "Movie"
  "TV Show"
  "Map"
}

Table collection {
  id "int identity" [primary key]
  title varchar
  annotations jsonb
}

Table stack {
  id "int identity" [primary key]
  room_id int [ref: > room.id]
}

Table room {
  id "int identity" [primary key]
  name varchar
}

Table tag {
  id "int identity" [primary key]
  name varchar
  description varchar
}

Table item_tag_link {
  tag_id int [ref: <> tag.id]
  item_id int [ref: <> item.id]

  indexes {
    (tag_id, item_id) [pk]
  }
}

Table collection_tag_link {
  tag_id int [ref: <> tag.id]
  collection_id int [ref: <> collection.id]

  indexes {
    (tag_id, collection_id) [pk]
  }
}

Table attachment {
  id "int identity" [primary key]
  item_id int [ref: > item.id]
  filename varchar
  filesize bigint
  checksum varchar
  mime_type varchar
}
```

_<https://dbdiagram.io/d/Library-67c4adb2263d6cf9a0f57ed3>_
