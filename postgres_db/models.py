from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UniqueConstraint, Float
from typing import Annotated
from postgres_db.core import Base
from postgres_db.core import str_512
import datetime
intpk = Annotated[int, mapped_column(primary_key=True)]

class DynamicsKeywordsOrm(Base):
    __tablename__ = 'dynamics_keyword'

    id: Mapped[intpk]
    keyword: Mapped[str_512]
    impressions: Mapped[int]
    dynamics_date: Mapped[datetime.date]

    unique_fields = ['keyword', 'dynamics_date']

    __table_args__ = (
        UniqueConstraint(
            *unique_fields, name='idx_keyword_date_unique'
            ),
    )

class RelatedKeywordsOrm(Base):
    __tablename__ = 'related_keywords'

    id: Mapped[intpk]
    parent_keyword: Mapped[str_512] = mapped_column(index=True)
    related_keyword: Mapped[str_512] = mapped_column()
    impressions: Mapped[int] = mapped_column()
    date_parsed: Mapped[datetime.date] = mapped_column(
            default=datetime.date.today
        )
    unique_fields = ['id', 'parent_keyword', 'related_keyword', 'date_parsed']

    __table_args__ = (
        UniqueConstraint(*unique_fields, name='idx_parent_related_date'),
    )

class DecompositionKeywordsOrm(Base):
    __tablename__ = 'decomposition_keyword'

    id: Mapped[intpk]
    keyword: Mapped[str_512]
    dynamics_date: Mapped[datetime.date]

    trend: Mapped[float | None] = mapped_column(Float, comment="Долгосрочная тенденция")
    seasonal: Mapped[float | None] = mapped_column(Float, comment="Сезонная составляющая")
    resid: Mapped[float | None] = mapped_column(Float, comment="Остаток (шум)")

    unique_fields = ['keyword', 'dynamics_date']

    __table_args__ = (
        UniqueConstraint(
            *unique_fields, name='idx_decomp_keyword_date_unique'
        ),
    )