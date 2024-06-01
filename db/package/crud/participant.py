from sqlalchemy.orm import Session

from .. import models


# ------
# Participant
# ------

def get(db: Session, discord_id: int) -> models.Participant | None:
    return db.query(models.Participant).filter(models.Participant.discord_account_id == discord_id).first()


def get_all(db: Session) -> list[models.Participant]:
    return db.query(models.Participant).all()


def create(
        db: Session,
        fullname: str,
        univ_name: str,
        discord_account_id: int
) -> models.Participant:
    db_participant = models.Participant(
        fullname=fullname,
        univ_name=univ_name,
        discord_account_id=discord_account_id
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant


def update(
        db: Session,
        participant: models.Participant,
        fullname: str,
        univ_name: str,
        discord_account_id: int
) -> models.Participant:
    participant.fullname = fullname
    participant.univ_name = univ_name
    participant.discord_account_id = discord_account_id
    db.commit()
    db.refresh(participant)
    return participant
