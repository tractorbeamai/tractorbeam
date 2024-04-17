from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .settings import get_settings

engine = create_async_engine(
    get_settings().database_url,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db():
    async with async_session() as session:
        yield session
