import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/promptab.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
    # Auto-migrate: add missing columns (SQLite doesn't support ADD COLUMN IF NOT EXISTS)
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("PRAGMA table_info(runs)"))
        run_columns = [row[1] for row in result]
        if "summary_metrics" not in run_columns:
            conn.execute(text("ALTER TABLE runs ADD COLUMN summary_metrics JSON DEFAULT '{}'"))
            conn.commit()
        result = conn.execute(text("PRAGMA table_info(experiments)"))
        exp_columns = [row[1] for row in result]
        if "parent_id" not in exp_columns:
            conn.execute(text("ALTER TABLE experiments ADD COLUMN parent_id TEXT"))
            conn.commit()
