from sqlmodel import Field, SQLModel


class FooItemBase(SQLModel):
    description: str
    public: bool


class FooItem(FooItemBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class FooItemCreate(FooItemBase):
    pass
