from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class ProcessingRun(Base):
    __tablename__ = "processing_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    input_filename: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    completed_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    settings_json: Mapped[str] = mapped_column(Text, default="{}")


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_file: Mapped[str] = mapped_column(String(255))
    source_sheet: Mapped[str] = mapped_column(String(255))
    source_row_number: Mapped[int] = mapped_column(Integer)
    company_name_raw: Mapped[str] = mapped_column(Text)
    company_name_normalized: Mapped[str] = mapped_column(Text)
    service_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approval_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approval_date: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    website_candidates = relationship("WebsiteCandidate", back_populates="company")
    extracted_contacts = relationship("ExtractedContact", back_populates="company")


class WebsiteCandidate(Base):
    __tablename__ = "website_candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    candidate_url: Mapped[str] = mapped_column(Text)
    root_domain: Mapped[str] = mapped_column(String(255))
    page_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_query: Mapped[str] = mapped_column(Text)
    candidate_rank: Mapped[int] = mapped_column(Integer)
    exact_name_match: Mapped[bool] = mapped_column(Boolean, default=False)
    fuzzy_name_score: Mapped[float] = mapped_column(Float, default=0)
    domain_similarity_score: Mapped[float] = mapped_column(Float, default=0)
    category_match_score: Mapped[float] = mapped_column(Float, default=0)
    nigeria_signal_score: Mapped[float] = mapped_column(Float, default=0)
    website_match_score: Mapped[float] = mapped_column(Float, default=0)
    accepted_boolean: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="website_candidates")


class ExtractedContact(Base):
    __tablename__ = "extracted_contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    accepted_website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_score: Mapped[float] = mapped_column(Float, default=0)
    final_confidence: Mapped[float] = mapped_column(Float, default=0)
    review_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="extracted_contacts")


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    field_name: Mapped[str] = mapped_column(String(100))
    field_value: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_kind: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
