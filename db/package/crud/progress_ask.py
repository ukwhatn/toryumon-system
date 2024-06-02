from sqlalchemy.orm import Session

from .. import models


# ------
# ProgressAsk
# ------

def get(db: Session, guild_id: int, ask_message_id: int) -> models.ProgressAsk | None:
    """
    進捗報告の情報を取得する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    guild_id : int
        対象GuildID
    ask_message_id : int
        進捗報告（公開側）のメッセージID

    Returns
    -------
    models.ProgressAsk | None
        ProgressAskモデル、なければNone
    """
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
    """
    進捗報告の情報を保存する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    guild_id : int
        対象GuildID
    ask_channel_id : int
        進捗報告（公開側）のチャンネルID
    ask_message_id : int
        進捗報告（公開側）のメッセージID
    summary_channel_id : int
        進捗管理（非公開側）のチャンネルID
    summary_message_id : int
        進捗管理（非公開側）のメッセージID
    role_ids : list[int]
        進捗報告の対象ロールID
    contents : list[str]
        手順のリスト

    Returns
    -------
    models.ProgressAsk
        ProgressAskモデル

    """
    # 進捗報告の情報を保存
    db_progress_ask = models.ProgressAsk(
        guild_id=guild_id,
        ask_channel_id=ask_channel_id,
        ask_message_id=ask_message_id,
        summary_channel_id=summary_channel_id,
        summary_message_id=summary_message_id
    )
    db.add(db_progress_ask)
    # idを取得するためにcommit
    db.commit()
    db.refresh(db_progress_ask)

    # 進捗報告の対象ロールと手順を保存
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

    # 最終commit
    db.commit()

    return db_progress_ask
