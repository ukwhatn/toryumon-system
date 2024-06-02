from sqlalchemy.orm import Session

from .. import models


# ------
# ProgressAsk
# ------

def get(db: Session, guild_id: int, ask_message_id: int) -> models.ProgressAsk | None:
    return db.query(models.ProgressAsk).filter(
        models.ProgressAsk.guild_id == guild_id,
        models.ProgressAsk.ask_message_id == ask_message_id
    ).first()


def create(
        db: Session,
        guild_id: int,
        ask_channel_id: int,
        ask_message_id: int,
        summary_channel_id: int,
        summary_message_id: int,
        role_ids: list[int],
        contents: list[str]
) -> models.ProgressAsk:
    db_progress_ask = models.ProgressAsk(
        guild_id=guild_id,
        ask_channel_id=ask_channel_id,
        ask_message_id=ask_message_id,
        summary_channel_id=summary_channel_id,
        summary_message_id=summary_message_id
    )
    db.add(db_progress_ask)
    db.commit()
    db.refresh(db_progress_ask)

    for role_id in role_ids:
        db_progress_ask_role = models.ProgressAskRoles(
            progress_ask_id=db_progress_ask.id,
            role_id=role_id
        )
        db.add(db_progress_ask_role)

    for content in contents:
        db_progress_ask_content = models.ProgressAskContents(
            progress_ask_id=db_progress_ask.id,
            content=content
        )
        db.add(db_progress_ask_content)

    db.commit()
    return db_progress_ask
