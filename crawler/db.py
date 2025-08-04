from sqlalchemy import create_engine, Column, String, Text, TIMESTAMP, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from .config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from .utils import normalize_url

Base = declarative_base()

class CourtCase(Base):
    __tablename__ = 'courtcases'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), unique=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('courtcases.id'), nullable=True)
    path_url = Column(Text)
    title = Column(Text)
    crawled_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    status_code = Column(Integer)

# Database URL
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()

def get_case_by_url(session, url):
    norm_url = normalize_url(url)
    if not norm_url:
        return None
    return session.query(CourtCase).filter(CourtCase.url == norm_url).first()

def insert_or_update_case(session, url, parent_id, path_url, title, status_code, is_check=True):
    norm_url = normalize_url(url)
    if not norm_url:
        return None
    
    if is_check:
        case = get_case_by_url(session, norm_url)
        if case:
            case.updated_at = func.now()
            case.status_code = status_code
            case.path_url = path_url
            case.title = title
            session.commit()
            return case.id
    
    # If not checking or case doesn't exist, insert new case
    new_case = CourtCase(
        url=norm_url,
        parent_id=parent_id,
        path_url=path_url,
        title=title,
        status_code=status_code
    )
    session.add(new_case)
    session.commit()
    return new_case.id 