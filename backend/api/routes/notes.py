"""Recruiter notes and candidate activity timeline."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from core.database import get_db
from core.models import RecruiterNote, ActivityLog, Candidate, User
from core.schemas import RecruiterNoteCreate, RecruiterNoteResponse, ActivityLogResponse
from api.dependencies import get_current_user

router = APIRouter()


def _log_activity(db: Session, candidate_id: UUID, actor_id: UUID, action: str, details: dict = None):
    db.add(ActivityLog(
        candidate_id=candidate_id,
        actor_id=actor_id,
        action=action,
        details=details or {},
    ))


@router.get("/candidates/{candidate_id}/notes", response_model=List[RecruiterNoteResponse])
def list_notes(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    notes = (
        db.query(RecruiterNote)
        .filter(RecruiterNote.candidate_id == candidate_id)
        .order_by(RecruiterNote.is_pinned.desc(), RecruiterNote.created_at.desc())
        .all()
    )

    author_ids = {n.author_id for n in notes}
    authors = {u.id: u for u in db.query(User).filter(User.id.in_(author_ids)).all()} if author_ids else {}

    return [
        RecruiterNoteResponse(
            id=n.id,
            candidate_id=n.candidate_id,
            author_id=n.author_id,
            author_name=authors.get(n.author_id).full_name or authors.get(n.author_id).email if authors.get(n.author_id) else None,
            content=n.content,
            is_pinned=n.is_pinned,
            created_at=n.created_at,
        )
        for n in notes
    ]


@router.post("/candidates/{candidate_id}/notes", response_model=RecruiterNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    candidate_id: UUID,
    payload: RecruiterNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    note = RecruiterNote(
        candidate_id=candidate_id,
        author_id=current_user.id,
        content=payload.content.strip(),
        is_pinned=payload.is_pinned,
    )
    db.add(note)
    _log_activity(db, candidate_id, current_user.id, "note_added", {"preview": payload.content[:100]})
    db.commit()
    db.refresh(note)

    return RecruiterNoteResponse(
        id=note.id,
        candidate_id=note.candidate_id,
        author_id=note.author_id,
        author_name=current_user.full_name or current_user.email,
        content=note.content,
        is_pinned=note.is_pinned,
        created_at=note.created_at,
    )


@router.delete("/candidates/{candidate_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    candidate_id: UUID,
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(RecruiterNote).filter(
        RecruiterNote.id == note_id,
        RecruiterNote.candidate_id == candidate_id,
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot delete another user's note")

    db.delete(note)
    _log_activity(db, candidate_id, current_user.id, "note_deleted", {"note_id": str(note_id)})
    db.commit()


@router.get("/candidates/{candidate_id}/timeline", response_model=List[ActivityLogResponse])
def get_timeline(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.candidate_id == candidate_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(50)
        .all()
    )

    actor_ids = {l.actor_id for l in logs if l.actor_id}
    actors = {u.id: u for u in db.query(User).filter(User.id.in_(actor_ids)).all()} if actor_ids else {}

    return [
        ActivityLogResponse(
            id=l.id,
            candidate_id=l.candidate_id,
            actor_name=(actors[l.actor_id].full_name or actors[l.actor_id].email) if l.actor_id and l.actor_id in actors else "System",
            action=l.action,
            details=l.details,
            created_at=l.created_at,
        )
        for l in logs
    ]
