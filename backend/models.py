from sqlalchemy import Column, String, LargeBinary
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    encrypted = Column(LargeBinary, nullable=False)
    embedding = Column(LargeBinary, nullable=False)