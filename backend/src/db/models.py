import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.db.engine import Base


class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    hypothesis = Column(Text, default="")
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    runs = relationship("Run", back_populates="experiment", cascade="all, delete-orphan")


class TestSet(Base):
    __tablename__ = "test_sets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    cases = relationship("TestCase", back_populates="test_set", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_set_id = Column(String, ForeignKey("test_sets.id", ondelete="CASCADE"), nullable=False)
    case_identifier = Column(String, nullable=False)
    category = Column(String, default="")
    input = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    test_set = relationship("TestSet", back_populates="cases")


class Rubric(Base):
    __tablename__ = "rubrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    dimensions = relationship("RubricDimension", back_populates="rubric", cascade="all, delete-orphan", order_by="RubricDimension.sort_order")


class RubricDimension(Base):
    __tablename__ = "rubric_dimensions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rubric_id = Column(String, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    weight = Column(Float, default=0.0)
    levels = Column(JSON, default=list)
    sort_order = Column(Integer, default=0)
    rubric = relationship("Rubric", back_populates="dimensions")


class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True)
    experiment_id = Column(String, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    config = Column(JSON, default=dict)
    prompt_names = Column(JSON, default=dict)
    prompt_models = Column(JSON, default=dict)
    total_cases = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    status = Column(String, default="pending")
    result_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    experiment = relationship("Experiment", back_populates="runs")
