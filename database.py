from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///rdp.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    division = Column(String)
    mentor = Column(String)
    specialty = Column(String)
    phase = Column(String)
    comments = Column(Text)
    score = Column(Integer)

Base.metadata.create_all(bind=engine)
