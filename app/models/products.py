from sqlalchemy import String, Integer, Boolean, Column, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.backend.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    slug = Column(String, unique=True, index=True)
    description = Column(String)
    price = Column(Integer)
    image_url = Column(String)
    stock = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'), )
    supplier_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    quantity_grades = Column(Integer, default=0)
    total_grades = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    category = relationship('Category', back_populates='products', uselist=False)


# if __name__ == '__main__':
#
#     from sqlalchemy.schema import CreateTable
#     print(CreateTable(Product.__table__))