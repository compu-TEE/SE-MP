from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    requirements = relationship(
        "Requirement",
        back_populates="project",
        cascade="all, delete"
    )


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))

    requirement_code = Column(String(50), nullable=False)
    statement = Column(Text, nullable=False)
    category = Column(String(100))
    source_stakeholder = Column(Text)
    business_justification = Column(Text)
    priority = Column(String(50))
    dependencies = Column(ARRAY(Text))
    assumptions = Column(ARRAY(Text))
    acceptance_criteria = Column(ARRAY(Text))
    applicable_regulations = Column(ARRAY(Text))
    risk_level = Column(String(50))
    confidence_score = Column(Float)
    approval_status = Column(String(50), default="pending")

    created_at = Column(DateTime, server_default=func.now())

    project = relationship(
        "Project",
        back_populates="requirements"
    )

class QualityAnalysis(Base):
    __tablename__ = "quality_analysis"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    completeness_score = Column(Float)
    summary = Column(Text)
    issues = Column(JSONB)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    project = relationship("Project")

class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    requirement_code = Column(String(50))
    status = Column(String(50))
    finding = Column(Text)
    evidence = Column(ARRAY(Text))
    recommendation = Column(Text)

    approval_status = Column(
        String(50),
        default="Draft"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    project = relationship("Project")

class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    requirement_code = Column(String(50))
    risk_type = Column(String(100))
    severity = Column(String(50))
    description = Column(Text)
    mitigation = Column(Text)
    approval_status = Column(String(20), default="Draft")

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    project = relationship("Project")

class SDLCRecommendation(Base):
    __tablename__ = "sdlc_recommendations"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    project_type = Column(String(100))
    regulatory_criticality = Column(String(50))
    change_frequency = Column(String(50))
    risk_level = Column(String(50))
    complexity = Column(String(50))
    delivery_priority = Column(String(50))
    requirements_clarity = Column(String(50))

    recommended_model = Column(String(100))
    reasoning = Column(Text)
    key_factors = Column(ARRAY(Text))
    approval_status = Column(String(20), default="Draft")

    project = relationship("Project")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)

    action = Column(String(50), nullable=False)

    old_status = Column(String(20))
    new_status = Column(String(20))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class DocumentationArtifact(Base):
    __tablename__ = "documentation_artifacts"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    artifact_type = Column(String(50))
    title = Column(String(255))
    content = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    project = relationship("Project")