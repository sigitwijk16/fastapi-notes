from datetime import datetime, timezone
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@router.post("/", response_model=schemas.NoteInDB, status_code=status.HTTP_201_CREATED)
def create_note_for_user(
    note: schemas.NoteCreate,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
):
    db_note = models.Note(**note.model_dump(), owner_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.get("/", response_model=List[schemas.NoteInDB])
def read_notes_for_user(
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    notes = db.query(models.Note).filter(models.Note.owner_id == current_user.id).offset(skip).limit(limit).all()
    return notes

@router.get("/{note_id}", response_model=schemas.NoteInDB)
def read_note(
    note_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note

@router.put("/{note_id}", response_model=schemas.NoteInDB)
def update_note(
    note_id: int,
    note: schemas.NoteUpdate,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    update_data = note.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_note, key, value)
    
    db_note.updated_at = datetime.now(timezone.utc)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(get_db)
):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == current_user.id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(db_note)
    db.commit()
    return None
