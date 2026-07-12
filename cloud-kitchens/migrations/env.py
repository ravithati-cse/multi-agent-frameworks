import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

# Import all models so Alembic sees them
from app.domains.orders.models import Order          # noqa
from app.domains.menu.models import MenuItem         # noqa
from app.domains.inventory.models import InventoryItem  # noqa
from app.domains.kitchen.models import Kitchen       # noqa
from app.domains.delivery.models import Delivery     # noqa
from app.domains.payments.models import Payment      # noqa
from app.domains.ticketing.models import Ticket      # noqa

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        await conn.run_sync(
            lambda sync_conn: context.configure(connection=sync_conn, target_metadata=target_metadata)
        )
        async with conn.begin():
            await conn.run_sync(lambda _: context.run_migrations())
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
