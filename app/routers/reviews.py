from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.products import Product
from app.models.user import User
from app.models.reviews import Review
from app.schemas import CreateReview
from .auth import get_current_user

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).where(Review.is_active == True))
    all_reviews = reviews.all()
    if not all_reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )

    return all_reviews


@router.get('/user/{username}')
async def user_reviews(db: Annotated[AsyncSession, Depends(get_db)], username: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no user found"
        )
    reviews = await db.scalars(select(Review).where(
        Review.user_id == user.id,
        Review.is_active == True),
    )
    all_user_reviews = reviews.all()
    if not all_user_reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )

    return all_user_reviews


@router.get('/product/{product_slug}')
async def product_reviews(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    reviews = await db.scalars(select(Review).where(
        Review.product_id == product.id,
        Review.is_active == True),
    )
    all_product_reviews = reviews.all()
    if not all_product_reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )

    return all_product_reviews


@router.post('/{product_slug}', status_code=status.HTTP_201_CREATED)
async def add_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str,
        create_review: CreateReview,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user:
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found"
            )
        await db.execute(insert(Review).values(
            comment=create_review.comment,
            grade=create_review.grade,
            user_id=get_user.get('id'),
            product_id=product.id,
        ))
        current_quantity_grades = 1
        if product.quantity_grades:
            current_quantity_grades += product.quantity_grades
        current_total_grades = create_review.grade
        if product.total_grades:
            current_total_grades += product.total_grades

        await db.execute(update(Product).where(Product.id == product.id).values(
            quantity_grades=current_quantity_grades,
            total_grades=current_total_grades,
            rating=round(current_total_grades / current_quantity_grades, 1)
        ))
        await db.commit()
        return {
            "status": status.HTTP_201_CREATED,
            "transaction": "Successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )


@router.delete('/{review_id}')
async def delete_review(
        db: Annotated[AsyncSession, Depends(get_db)],
        review_id: int,
        get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user and get_user.get('is_admin'):
        review = await db.scalar(select(Review).where(Review.id == review_id, Review.is_active == True))
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no comment found",
            )
        product = await db.scalar(select(Product).where(Product.id == review.product_id))
        if product:
            current_quantity_grades = product.quantity_grades - 1
            current_total_grades = product.total_grades - review.grade
            product.quantity_grades = current_quantity_grades
            product.total_grades = current_total_grades
            if current_quantity_grades > 0:
                product.rating = round(current_total_grades / current_quantity_grades, 1)
            else:
                product.rating = 0.0
        review.is_active = False

        await db.commit()
        return {
            "status": status.HTTP_200_OK,
            "transaction": "Review delete is successful",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )
