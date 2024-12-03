
from sqlalchemy import Column, Integer, String
from app.database import Base

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    document_path = Column(String, nullable=False)
    image_path = Column(String, nullable=False)
