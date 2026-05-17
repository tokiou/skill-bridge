from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Protocol):
    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


class SqlAlchemyUnitOfWork:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
