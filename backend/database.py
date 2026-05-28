"""
Configuración de SQLAlchemy con soporte async e inicialización de tipos de usuario.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def init_db():
    from models import TipoUsuario

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        tipos_existentes = await session.execute(select(TipoUsuario.nombre))
        existentes = {row[0] for row in tipos_existentes.all()}
        tipos_requeridos = {"admin", "paciente", "doctor", "administrativo"}
        for tipo in tipos_requeridos - existentes:
            session.add(TipoUsuario(nombre=tipo))
        await session.commit()

    print("[DB] Tablas creadas y tipos de usuario inicializados")

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise