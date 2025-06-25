from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import create_access_token


def test_read_root(test_client: TestClient):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI."}

class TestUsers:
    def test_register_user_success(self, test_client: TestClient, db_session: Session):
        response = test_client.post(
            "/users/register",
            json={"email": "newuser@example.com", "password": "newpassword"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        
        user = db_session.query(models.User).filter(models.User.email == "newuser@example.com").first()
        assert user is not None

    def test_register_user_duplicate_email(self, test_client: TestClient, test_user: models.User):
        response = test_client.post(
            "/users/register",
            json={"email": test_user.email, "password": "anotherpassword"},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Email already registered"}

    def test_login_success(self, test_client: TestClient, test_user: models.User):
        response = test_client.post(
            "/users/token",
            data={"username": test_user.email, "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client: TestClient, test_user: models.User):
        response = test_client.post(
            "/users/token",
            data={"username": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect email or password"}

    def test_login_wrong_email(self, test_client: TestClient):
        response = test_client.post(
            "/users/token",
            data={"username": "wrong@example.com", "password": "password123"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect email or password"}

    def test_read_me(self, test_client: TestClient, test_user: models.User, auth_headers: dict):
        response = test_client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id


class TestNotes:
    def test_create_note(self, test_client: TestClient, auth_headers: dict, db_session: Session):
        note_data = {"title": "Test Note", "content": "This is a test note."}
        response = test_client.post("/notes/", json=note_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == note_data["title"]
        assert data["content"] == note_data["content"]
        assert "id" in data
        assert "owner_id" in data

        note = db_session.query(models.Note).filter(models.Note.id == data["id"]).first()
        assert note is not None
        assert note.title == note_data["title"]

    def test_read_notes_for_user(self, test_client: TestClient, test_user: models.User, auth_headers: dict, db_session: Session):
        db_session.add(models.Note(title="Note 1", content="Content 1", owner_id=test_user.id))
        db_session.add(models.Note(title="Note 2", content="Content 2", owner_id=test_user.id))
        db_session.commit()

        response = test_client.get("/notes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Note 1"
        assert data[1]["title"] == "Note 2"

    def test_read_single_note(self, test_client: TestClient, test_user: models.User, auth_headers: dict, db_session: Session):
        note = models.Note(title="Specific Note", content="Content", owner_id=test_user.id)
        db_session.add(note)
        db_session.commit()

        response = test_client.get(f"/notes/{note.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Specific Note"
        assert data["id"] == note.id

    def test_read_note_not_found(self, test_client: TestClient, auth_headers: dict):
        response = test_client.get("/notes/9999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json() == {"detail": "Note not found"}

    def test_update_note(self, test_client: TestClient, test_user: models.User, auth_headers: dict, db_session: Session):
        note = models.Note(title="Original Title", content="Original Content", owner_id=test_user.id)
        db_session.add(note)
        db_session.commit()

        update_data = {"title": "Updated Title", "content": "Updated Content"}
        response = test_client.put(f"/notes/{note.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated Content"
        assert data["id"] == note.id

        db_session.refresh(note)
        assert note.title == "Updated Title"

    def test_delete_note(self, test_client: TestClient, test_user: models.User, auth_headers: dict, db_session: Session):
        note = models.Note(title="To Be Deleted", content="Content", owner_id=test_user.id)
        db_session.add(note)
        db_session.commit()
        note_id = note.id

        response = test_client.delete(f"/notes/{note_id}", headers=auth_headers)
        assert response.status_code == 204

        deleted_note = db_session.query(models.Note).filter(models.Note.id == note_id).first()
        assert deleted_note is None
        
    def test_user_cannot_access_another_users_note(self, test_client: TestClient, test_user: models.User, db_session: Session):
        other_user = models.User(email="other@example.com", hashed_password="pw")
        db_session.add(other_user)
        db_session.commit()
        
        other_note = models.Note(title="Other's Note", content="Secret", owner_id=other_user.id)
        db_session.add(other_note)
        db_session.commit()
        
        access_token = create_access_token(data={"sub": test_user.email})
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        response = test_client.get(f"/notes/{other_note.id}", headers=auth_headers)
        assert response.status_code == 404