from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[Optional[str]]
    text: Mapped[str]

    tenant_id: Mapped[str] = mapped_column(index=True)
    tenant_user_id: Mapped[str] = mapped_column(index=True)

    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="document")

    def __repr__(self) -> str:
        return f"Document(id={self.id}, title={self.title})"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    document_id: Mapped[int] = mapped_column(foreign_key="documents.id")
    text: Mapped[str]

    tenant_id: Mapped[str] = mapped_column(index=True)
    tenant_user_id: Mapped[str] = mapped_column(index=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"Chunk(id={self.id}, document_id={self.document_id})"
