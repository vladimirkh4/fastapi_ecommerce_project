from sqlalchemy import Column, Boolean, Date, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    comment = Column(String, nullable=True)
    comment_date = Column(Date, default=datetime.utcnow().date())
    grade = Column(Integer)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))