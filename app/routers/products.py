from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from slugify import slugify
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.category import Category
from app.models.products import Product
from app.schemas import CreateProduct
from .auth import get_current_user

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).join(Category).where(
        Product.is_active == True,
        Category.is_active == True,
        Product.stock > 0,
    ))
    products = products.all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no products'
        )

    return products


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        create_product: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        category = await db.scalar(select(Category).where(Category.id == create_product.category))

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found',
            )
        await db.execute(insert(Product).values(
            name=create_product.name,
            slug=slugify(create_product.name),
            description=create_product.description,
            price=create_product.price,
            image_url=create_product.image_url,
            stock=create_product.stock,
            category_id=create_product.category,
            supplier_id=get_user.get('id')
        ))
        await db.commit()
        return {
            "status": status.HTTP_201_CREATED,
            "transaction": "Successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category found",
        )

    category_id_list = [category.id, ]
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))

    subcategories = subcategories.all()
    for subcategory in subcategories:
        category_id_list.append(subcategory.id)

    products = await db.scalars(select(Product).where(
        Product.category_id.in_(category_id_list),
        Product.stock > 0,
        Product.is_active == True,
    ))

    products = products.all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )

    return products


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(
        Product.slug == product_slug,
        Product.is_active == True,
        Product.stock > 0,
    ))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found",
        )
    return product


@router.put('/{product_slug}')
async def update_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str,
        update_product: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found",
            )
        if get_user.get('is_supplier') and product.supplier_id != get_user.get('id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to use this method",
            )

        product.name = update_product.name
        product.slug = slugify(update_product.name)
        product.description = update_product.description
        product.price = update_product.price
        product.image_url = update_product.image_url
        product.stock = update_product.stock
        product.category_id = update_product.category

        await db.commit()
        return {
            "status": status.HTTP_200_OK,
            "transaction": "Product update is successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )


@router.delete('/{product_slug}')
async def delete_product(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str,
        get_user: Annotated[dict, Depends(get_current_user)],
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product found",
            )

        if get_user.get('is_supplier') and product.supplier_id != get_user.get('id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to use this method",
            )

        product.is_active = False
        await db.commit()
        return {
            "status": status.HTTP_200_OK,
            "transaction": "Product delete is successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method",
        )
