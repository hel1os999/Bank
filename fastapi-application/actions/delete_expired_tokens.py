from datetime import datetime, timedelta

from sqlalchemy import delete


from core.models import AccessToken
from core.models.userdata_db_helper import userdata_db_helper

async def delete_expired_tokens():
    async with userdata_db_helper.session_factory() as session:
        expiration_threshold = datetime.now() - timedelta(minutes=5)

        stmt = (
            delete(AccessToken)
            .where(AccessToken.created_at < expiration_threshold)
        )

        await session.execute(stmt)
        await session.commit()


