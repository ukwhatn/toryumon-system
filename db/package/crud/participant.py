import re

from sqlalchemy.orm import Session

from .. import models


# ------
# Utility
# ------
def normalizer_spaces(s: str) -> str:
    """
    正規表現で全ての空白（半角・全角問わず）を除去する

    Parameters
    ----------
    s : str
        文字列

    Returns
    -------
    str
        全ての空白を除去した文字列
    """
    return re.sub(r"[\s 　]", "", s)


# ------
# Participant
# ------
def normalizer_fullname(fullname: str) -> str:
    """
    参加者のフルネームを正規化する

    Parameters
    ----------
    fullname : str
        参加者のフルネーム

    Returns
    -------
    str
        正規化されたフルネーム
    """
    return normalizer_spaces(fullname)


def normalizer_univ_name(univ_name: str) -> str:
    """
    参加者の大学名を正規化する

    Parameters
    ----------
    univ_name : str
        参加者の大学名

    Returns
    -------
    str
        正規化された大学名
    """
    return normalizer_spaces(univ_name)


def validates(participant: models.Participant) -> bool:
    """
    参加者の情報が正しいかどうかを検証する

    Parameters
    ----------
    participant : models.Participant
        参加者モデル

    Returns
    -------
    bool
        参加者の情報が正しい場合はTrue、正しくない場合はFalse
    """
    return participant.fullname != "" and participant.univ_name != ""


def get(db: Session, discord_id: int) -> models.Participant | None:
    """
    参加者のDiscord User IDからParticipantモデルを取得する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    discord_id : int
        参加者のDiscord User ID

    Returns
    -------
    models.Participant | None
        見つかったParticipantモデル、見つからなかった場合はNone
    """
    return db.query(models.Participant).filter(models.Participant.discord_account_id == discord_id).first()


def get_all(db: Session) -> list[models.Participant]:
    """
    全ての参加者を取得する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション

    Returns
    -------
    list[models.Participant]
        全てのParticipantモデル
    """
    return db.query(models.Participant).all()


def create(
        db: Session,
        fullname: str,
        univ_name: str,
        discord_account_id: int
) -> models.Participant | None:
    """
    新しい参加者を作成する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    fullname : str
        参加者のフルネーム
    univ_name : str
        参加者の大学名
    discord_account_id : int
        参加者のDiscord ID

    Returns
    -------
    models.Participant | None
        新しく作成されたParticipantモデル
        エラーが発生した場合はNone
    """
    # 新しいParticipantモデルを作成
    db_participant = models.Participant(
        fullname=normalizer_fullname(fullname),
        univ_name=normalizer_univ_name(univ_name),
        discord_account_id=discord_account_id
    )
    # バリデーション
    if not validates(db_participant):
        return None

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
) -> models.Participant | None:
    """
    参加者の情報を更新する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    participant : models.Participant
        更新するParticipantモデル
    fullname : str
        更新するフルネーム
    univ_name : str
        更新する大学名
    discord_account_id : int
        更新するDiscord ID
    """
    participant.fullname = normalizer_fullname(fullname)
    participant.univ_name = normalizer_univ_name(univ_name)
    participant.discord_account_id = discord_account_id

    # バリデーション
    if not validates(participant):
        return None

    db.commit()
    db.refresh(participant)
    return participant


def create_or_update(
        db: Session,
        fullname: str,
        univ_name: str,
        discord_account_id: int
) -> models.Participant | None:
    """
    参加者が存在しない場合は新しく作成し、存在する場合は情報を更新する

    Parameters
    ----------
    db : Session
        SQLAlchemyで確立したセッション
    fullname : str
        参加者のフルネーム
    univ_name : str
        参加者の大学名
    discord_account_id : int
        参加者のDiscord ID

    Returns
    -------
    models.Participant
        新しく作成されたParticipantモデル、または更新されたParticipantモデル
    """
    participant = get(db, discord_account_id)

    if participant is not None:
        return update(db, participant, fullname, univ_name, discord_account_id)

    return create(db, fullname, univ_name, discord_account_id)
