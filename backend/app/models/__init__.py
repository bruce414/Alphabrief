"""SQLAlchemy models package.

Import each model module here as you add tables so classes register on ``Base.metadata``
and Alembic ``--autogenerate`` can detect them.

Shared column mixins live in ``app.models.base``.

Example::

    from app.models.user import User  # noqa: F401

"""

__all__: list[str] = []
