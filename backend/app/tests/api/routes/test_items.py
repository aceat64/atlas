from fastapi.testclient import TestClient
from sqlmodel import Session

from app.tests.utils.item import create_random_item


def test_create_item(client: TestClient) -> None:
    data = {"title": "The Hitchhiker's Guide to the Galaxy", "item_type": "book"}
    response = client.post("/items", json=data)
    assert response.status_code == 200
    content = response.json()
    assert "id" in content
    assert content["title"] == data["title"]
    assert content["item_type"] == data["item_type"]
    assert content["collection_id"] is None
    assert content["stack_id"] is None
    assert content["shelf"] is None
    assert content["slot"] is None
    assert content["annotations"] == {}


def test_read_item(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    response = client.get(f"/items/{item.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == item.id
    assert content["title"] == item.title
    assert content["item_type"] == item.item_type
    assert content["collection_id"] == item.collection_id
    assert content["stack_id"] == item.stack_id
    assert content["shelf"] == item.shelf
    assert content["slot"] == item.slot
    assert content["annotations"] == item.annotations


def test_read_item_not_found(client: TestClient) -> None:
    response = client.get("/items/2147483647")
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_items(client: TestClient, db: Session) -> None:
    create_random_item(db)
    create_random_item(
        db, create_collection=False, create_stack=False, create_shelf=False, create_slot=False
    )
    response = client.get("/items/")
    assert response.status_code == 200
    content = response.json()
    assert len(content["items"]) >= 2


def test_update_item(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title"}
    response = client.put(f"/items/{item.id}", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == item.id
    assert content["title"] == data["title"]
    assert content["item_type"] == item.item_type
    assert content["collection_id"] == item.collection_id
    assert content["stack_id"] == item.stack_id
    assert content["shelf"] == item.shelf
    assert content["slot"] == item.slot
    assert content["annotations"] == item.annotations


def test_update_item_item_type(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    data = {"item_type": "movie"}
    response = client.put(f"/items/{item.id}", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == item.id
    assert content["title"] == item.title
    assert content["item_type"] == data["item_type"]
    assert content["collection_id"] == item.collection_id
    assert content["stack_id"] == item.stack_id
    assert content["shelf"] == item.shelf
    assert content["slot"] == item.slot
    assert content["annotations"] == item.annotations


def test_update_item_annotations(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    data = {"annotations": {"foo": "bar"}}
    response = client.put(f"/items/{item.id}", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == item.id
    assert content["title"] == item.title
    assert content["item_type"] == item.item_type
    assert content["collection_id"] == item.collection_id
    assert content["stack_id"] == item.stack_id
    assert content["shelf"] == item.shelf
    assert content["slot"] == item.slot
    assert content["annotations"] == data["annotations"]


def test_update_item_not_found(client: TestClient) -> None:
    data = {"title": "Updated title"}
    response = client.put("/items/2147483647", json=data)
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item(client: TestClient, db: Session) -> None:
    item = create_random_item(db)
    response = client.delete(f"/items/{item.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["detail"] == "Item deleted successfully"


def test_delete_item_not_found(client: TestClient) -> None:
    response = client.delete("/items/2147483647")
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"
