from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.db.models import Experiment, TestSet, TestCase, Rubric, RubricDimension, Run


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

def create_experiment(db: Session, name: str, description: str = "", hypothesis: str = "", config: dict | None = None) -> Experiment:
    exp = Experiment(name=name, description=description, hypothesis=hypothesis, config=config)
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
    db: Session, id: str, name: str, description: str = "", hypothesis: str = "", config: dict | None = None
) -> Experiment | None:
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if exp is None:
        return None
    exp.name = name
    exp.description = description
    exp.hypothesis = hypothesis
    exp.config = config
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
) -> Run:
    run = Run(
        id=run_id,
        experiment_id=experiment_id,
        config=config,
        prompt_names=prompt_names,
        prompt_models=prompt_models,
        total_cases=total_cases,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


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
