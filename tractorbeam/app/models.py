from sqlalchemy import ForeignKey, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    # https://github.com/rhoboro/async-fastapi-sqlalchemy/blob/main/app/models/base.py
    __abstract__ = True
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    content: Mapped[str]

    tenant_id: Mapped[str] = mapped_column(index=True)
    tenant_user_id: Mapped[str] = mapped_column(index=True)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")

    def __repr__(self) -> str:
        return f'Document(id={self.id}, title="{self.title}")'


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    content: Mapped[str]

    tenant_id: Mapped[str] = mapped_column(index=True)
    tenant_user_id: Mapped[str] = mapped_column(index=True)

    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f'Chunk(id={self.id}, document_id={self.document_id}, content="{self.content}")'
