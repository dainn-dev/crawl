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

def cleanup_duplicate_urls():
    """Clean up duplicate URLs in the database"""
    session = get_session()
    try:
        # Find all URLs that have duplicates
        from sqlalchemy import func
        duplicates = session.query(
            CourtCase.url,
            func.count(CourtCase.id).label('count')
        ).group_by(CourtCase.url).having(func.count(CourtCase.id) > 1).all()
        
        cleaned_count = 0
        for url, count in duplicates:
            # Get all cases with this URL
            cases = session.query(CourtCase).filter(CourtCase.url == url).order_by(CourtCase.crawled_at).all()
            
            # Keep the first one (oldest), delete the rest
            for duplicate_case in cases[1:]:
                session.delete(duplicate_case)
                cleaned_count += 1
        
        session.commit()
        print(f"Cleaned up {cleaned_count} duplicate records")
        return cleaned_count
    except Exception as e:
        session.rollback()
        print(f"Error cleaning up duplicates: {e}")
        return 0
    finally:
        session.close()

def check_duplicate_urls():
    """Check for duplicate URLs in the database"""
    session = get_session()
    try:
        from sqlalchemy import func
        duplicates = session.query(
            CourtCase.url,
            func.count(CourtCase.id).label('count')
        ).group_by(CourtCase.url).having(func.count(CourtCase.id) > 1).all()
        
        if duplicates:
            print(f"Found {len(duplicates)} URLs with duplicates:")
            for url, count in duplicates:
                print(f"  {url}: {count} records")
            return duplicates
        else:
            print("No duplicate URLs found")
            return []
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return []
    finally:
        session.close()

def normalize_existing_urls():
    """Normalize existing URLs in the database by removing www prefixes"""
    session = get_session()
    try:
        from urllib.parse import urlparse, urlunparse
        
        # Find all records with www prefix (both http and https)
        www_records = session.query(CourtCase).filter(
            CourtCase.url.like('http://www.%')
        ).all()
        
        https_www_records = session.query(CourtCase).filter(
            CourtCase.url.like('https://www.%')
        ).all()
        
        www_records.extend(https_www_records)
        
        normalized_count = 0
        for record in www_records:
            try:
                parsed = urlparse(record.url)
                if parsed.netloc.startswith('www.'):
                    # Remove www prefix
                    new_netloc = parsed.netloc[4:]
                    new_url = urlunparse(parsed._replace(netloc=new_netloc))
                    
                    # Check if normalized URL already exists
                    existing = session.query(CourtCase).filter(CourtCase.url == new_url).first()
                    if existing:
                        # If normalized URL exists, delete the www version
                        session.delete(record)
                        print(f"Deleted duplicate: {record.url} -> {new_url}")
                    else:
                        # Update the URL
                        record.url = new_url
                        print(f"Normalized: {record.url} -> {new_url}")
                    
                    normalized_count += 1
            except Exception as e:
                print(f"Error normalizing {record.url}: {e}")
        
        session.commit()
        print(f"Normalized {normalized_count} URLs")
        return normalized_count
    except Exception as e:
        session.rollback()
        print(f"Error normalizing URLs: {e}")
        return 0
    finally:
        session.close()

def insert_or_update_case(session, url, parent_id, path_url, title, status_code, is_check=True):
    norm_url = normalize_url(url)
    if not norm_url:
        return None
    
    if is_check:
        # Check if case exists - get the first one if multiple exist
        case = get_case_by_url(session, norm_url)
        if case:
            try:
                # Update the existing case
                case.updated_at = func.now()
                case.status_code = status_code
                case.path_url = path_url
                case.title = title
                session.commit()
                return case.id
            except Exception as e:
                # If update fails due to duplicates, try to handle it
                session.rollback()
                # Get all cases with this URL and delete duplicates
                cases = session.query(CourtCase).filter(CourtCase.url == norm_url).all()
                if len(cases) > 1:
                    # Keep the first one, delete the rest
                    for duplicate_case in cases[1:]:
                        session.delete(duplicate_case)
                    session.commit()
                    # Now update the remaining case
                    case = cases[0]
                    case.updated_at = func.now()
                    case.status_code = status_code
                    case.path_url = path_url
                    case.title = title
                    session.commit()
                    return case.id
                else:
                    # Re-raise the original exception if it's not a duplicate issue
                    raise e
    
    # If not checking or case doesn't exist, insert new case
    try:
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
    except Exception as e:
        # If insert fails due to duplicate URL, try to update existing
        session.rollback()
        case = get_case_by_url(session, norm_url)
        if case:
            case.updated_at = func.now()
            case.status_code = status_code
            case.path_url = path_url
            case.title = title
            session.commit()
            return case.id
        else:
            # Re-raise if it's not a duplicate issue
            raise e 