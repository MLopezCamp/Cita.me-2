"""Configuración de SQLAlchemy con soporte async."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL

# Motor async con SQLite
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Fábrica de sesiones async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


async def init_db():
    """Crear todas las tablas al iniciar la aplicación."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tablas creadas/verificadas correctamente")


async def get_session() -> AsyncSession:
    """Dependencia que provee una sesión de base de datos async."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise