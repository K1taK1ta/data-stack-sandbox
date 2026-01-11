from postgres_db.core import session_factory, sync_engine, Base
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select


class DataAccess():

    @staticmethod
    def create_table():
        Base.metadata.create_all(sync_engine)

    @staticmethod
    def read_table(model):
        with session_factory() as session:
            # query = Select(model)
            # result = session.execute(query)
            # table = result.scalars().all()

            query = select(model.__table__)
            result = session.execute(query)

        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    def insert_table(model, data: list):
        with session_factory() as session:
            stmt = insert(model).values(data)
            session.execute(stmt)
            session.commit()

    @staticmethod
    def upsert_table(model, data: list):
        with session_factory() as session:
            stmt = insert(model).values(data)
            keys = getattr(model, 'unique_fields', [])

            update_cols = {
                c.name: stmt.excluded[c.name]
                for c in model.__table__.columns
                if c.name not in keys and c.name != 'id'
            }

            if not update_cols:
                upsert_stmt = stmt.on_conflict_do_nothing(
                    index_elements=keys)

            else:
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=keys,
                    set_=update_cols
                )

            session.execute(upsert_stmt)
            session.commit()