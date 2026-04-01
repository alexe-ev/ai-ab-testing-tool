from datetime import datetime, timezone
from sqlalchemy import func, text, asc, desc
from sqlalchemy.orm import Session
from src.db.models import Experiment, TestSet, TestCase, Rubric, RubricDimension, Run, Setting


# ─── Test Sets ────────────────────────────────────────────────────

def create_test_set(db: Session, name: str, cases: list[dict]) -> TestSet:
    ts = TestSet(name=name)
    db.add(ts)
    db.flush()
    for case in cases:
        tc = TestCase(
            test_set_id=ts.id,
            case_identifier=case.get("case_identifier", ""),
            category=case.get("category", ""),
            input=case["input"],
            context=case.get("context"),
            reference=case.get("reference"),
        )
        db.add(tc)
    db.commit()
    db.refresh(ts)
    return ts


def get_test_set(db: Session, id: str) -> TestSet | None:
    return db.query(TestSet).filter(TestSet.id == id).first()


def list_test_sets(db: Session) -> list[tuple]:
    return (
        db.query(TestSet, func.count(TestCase.id).label("case_count"))
        .outerjoin(TestCase)
        .group_by(TestSet.id)
        .all()
    )


def update_test_set(db: Session, id: str, name: str, cases: list[dict]) -> TestSet | None:
    ts = db.query(TestSet).filter(TestSet.id == id).first()
    if ts is None:
        return None
    ts.name = name
    ts.updated_at = datetime.now(timezone.utc)
    ts.cases = [
        TestCase(
            test_set_id=ts.id,
            case_identifier=case.get("case_identifier", ""),
            category=case.get("category", ""),
            input=case["input"],
            context=case.get("context"),
            reference=case.get("reference"),
        )
        for case in cases
    ]
    db.commit()
    db.refresh(ts)
    return ts


def delete_test_set(db: Session, id: str) -> bool:
    ts = db.query(TestSet).filter(TestSet.id == id).first()
    if ts is None:
        return False
    db.delete(ts)
    db.commit()
    return True


# ─── Rubrics ──────────────────────────────────────────────────────

def create_rubric(db: Session, name: str, dimensions: list[dict]) -> Rubric:
    rubric = Rubric(name=name)
    db.add(rubric)
    db.flush()
    for i, dim in enumerate(dimensions):
        rd = RubricDimension(
            rubric_id=rubric.id,
            name=dim["name"],
            description=dim.get("description", ""),
            weight=dim.get("weight", 0.0),
            levels=dim.get("levels", []),
            sort_order=i,
        )
        db.add(rd)
    db.commit()
    db.refresh(rubric)
    return rubric


def get_rubric(db: Session, id: str) -> Rubric | None:
    return db.query(Rubric).filter(Rubric.id == id).first()


def list_rubrics(db: Session) -> list[Rubric]:
    return db.query(Rubric).all()


def update_rubric(db: Session, id: str, name: str, dimensions: list[dict]) -> Rubric | None:
    rubric = db.query(Rubric).filter(Rubric.id == id).first()
    if rubric is None:
        return None
    rubric.name = name
    rubric.updated_at = datetime.now(timezone.utc)
    rubric.dimensions = [
        RubricDimension(
            rubric_id=rubric.id,
            name=dim["name"],
            description=dim.get("description", ""),
            weight=dim.get("weight", 0.0),
            levels=dim.get("levels", []),
            sort_order=i,
        )
        for i, dim in enumerate(dimensions)
    ]
    db.commit()
    db.refresh(rubric)
    return rubric


def delete_rubric(db: Session, id: str) -> bool:
    rubric = db.query(Rubric).filter(Rubric.id == id).first()
    if rubric is None:
        return False
    db.delete(rubric)
    db.commit()
    return True


# ─── Experiments ──────────────────────────────────────────────────

def create_experiment(db: Session, name: str, description: str = "", hypothesis: str = "", config: dict | None = None, parent_id: str | None = None) -> Experiment:
    exp = Experiment(name=name, description=description, hypothesis=hypothesis, config=config, parent_id=parent_id)
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def get_experiment(db: Session, id: str) -> Experiment | None:
    return db.query(Experiment).filter(Experiment.id == id).first()


def list_experiments(db: Session) -> list[tuple]:
    return (
        db.query(Experiment, func.count(Run.id).label("run_count"))
        .outerjoin(Run)
        .group_by(Experiment.id)
        .all()
    )


def update_experiment(
    db: Session, id: str, name: str, description: str = "", hypothesis: str = "", config: dict | None = None, parent_id: str | None = None
) -> Experiment | None:
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if exp is None:
        return None
    exp.name = name
    exp.description = description
    exp.hypothesis = hypothesis
    exp.config = config
    exp.parent_id = parent_id
    exp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exp)
    return exp


def delete_experiment(db: Session, id: str) -> bool:
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if exp is None:
        return False
    db.delete(exp)
    db.commit()
    return True


# ─── Runs ─────────────────────────────────────────────────────────

def create_run(
    db: Session,
    run_id: str,
    experiment_id: str | None,
    config: dict,
    prompt_names: dict,
    prompt_models: dict,
    total_cases: int,
    status: str = "pending",
) -> Run:
    run = Run(
        id=run_id,
        experiment_id=experiment_id,
        config=config,
        prompt_names=prompt_names,
        prompt_models=prompt_models,
        total_cases=total_cases,
        status=status,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> Run | None:
    return db.query(Run).filter(Run.id == run_id).first()


def list_experiment_runs(db: Session, experiment_id: str) -> list[Run]:
    return db.query(Run).filter(Run.experiment_id == experiment_id).order_by(Run.created_at.desc()).all()


def list_runs(
    db: Session,
    experiment_id: str | None = None,
    status: str | None = None,
    model: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[tuple], int]:
    """Return (list of (Run, experiment_name), total_count)."""
    query = (
        db.query(Run, Experiment.name.label("experiment_name"))
        .outerjoin(Experiment, Run.experiment_id == Experiment.id)
    )

    if experiment_id is not None:
        query = query.filter(Run.experiment_id == experiment_id)
    if status is not None:
        query = query.filter(Run.status == status)
    if model is not None:
        # Filter by model name appearing in prompt_models JSON values
        query = query.filter(Run.prompt_models.contains(model))

    total = query.count()

    VALID_SORT_BY = {"score_delta", "created_at"}
    effective_sort_by = sort_by if sort_by in VALID_SORT_BY else "created_at"

    if effective_sort_by == "score_delta":
        # JSON path extraction for SQLite
        order_expr = text("json_extract(runs.summary_metrics, '$.score_delta')")
        if sort_order == "asc":
            query = query.order_by(asc(order_expr))
        else:
            query = query.order_by(desc(order_expr))
    else:
        col = Run.created_at
        if sort_order == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())

    rows = query.offset(offset).limit(limit).all()
    return rows, total


def update_run_summary_metrics(db: Session, run_id: str, metrics: dict) -> Run | None:
    run = db.query(Run).filter(Run.id == run_id).first()
    if run is None:
        return None
    run.summary_metrics = metrics
    db.commit()
    db.refresh(run)
    return run


def list_experiments_with_last_run(db: Session) -> list[tuple]:
    """Return list of (Experiment, run_count, last_run_at, last_run_metrics).

    Uses a single query: subquery finds the max completed_at per experiment for
    complete runs, then joins back to Run to get that row's summary_metrics.
    """
    # Subquery: max completed_at per experiment_id among complete runs
    latest_sq = (
        db.query(
            Run.experiment_id.label("experiment_id"),
            func.max(Run.completed_at).label("max_completed_at"),
        )
        .filter(Run.status == "complete")
        .group_by(Run.experiment_id)
        .subquery()
    )

    # Alias for the last complete Run row (joined on experiment_id + completed_at)
    LastRun = db.query(Run).join(
        latest_sq,
        (Run.experiment_id == latest_sq.c.experiment_id)
        & (Run.completed_at == latest_sq.c.max_completed_at),
    ).subquery()

    rows = (
        db.query(
            Experiment,
            func.count(Run.id).label("run_count"),
            LastRun.c.completed_at.label("last_run_at"),
            LastRun.c.summary_metrics.label("last_run_metrics"),
        )
        .outerjoin(Run, Run.experiment_id == Experiment.id)
        .outerjoin(LastRun, LastRun.c.experiment_id == Experiment.id)
        .group_by(Experiment.id, LastRun.c.completed_at, LastRun.c.summary_metrics)
        .all()
    )

    return [
        (exp, run_count, last_run_at, last_run_metrics)
        for exp, run_count, last_run_at, last_run_metrics in rows
    ]


def update_run_status(
    db: Session,
    run_id: str,
    status: str,
    result_path: str | None = None,
    error_count: int | None = None,
) -> Run | None:
    run = db.query(Run).filter(Run.id == run_id).first()
    if run is None:
        return None
    run.status = status
    if result_path is not None:
        run.result_path = result_path
    if error_count is not None:
        run.error_count = error_count
    if status in ("complete", "failed"):
        run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


# ─── Settings ────────────────────────────────────────────────────

def get_setting(db: Session, key: str) -> Setting | None:
    return db.query(Setting).filter(Setting.key == key).first()


def upsert_setting(db: Session, key: str, value: str) -> Setting:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting is None:
        setting = Setting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
        setting.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(setting)
    return setting


def list_settings(db: Session) -> list[Setting]:
    return db.query(Setting).all()


def delete_setting(db: Session, key: str) -> bool:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting is None:
        return False
    db.delete(setting)
    db.commit()
    return True
