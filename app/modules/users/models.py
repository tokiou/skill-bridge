from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="America/Argentina/Buenos_Aires",
    )

    reputation_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped["User"] = relationship(
        back_populates="oauth_accounts",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_oauth_accounts_provider_provider_user_id",
        ),
    )