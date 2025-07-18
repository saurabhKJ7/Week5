import asyncio
import random
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models import (
    Platform, Category, Brand, Product, ProductPrice, ProductAvailability, Currency, UOM, Tax, Location
)

fake = Faker()

async def seed_data():
    async with SessionLocal() as session:
        # Create Currencies
        inr, _ = await get_or_create(session, Currency, code="INR", name="Indian Rupee")

        # Create UOMs
        kg, _ = await get_or_create(session, UOM, name="kg")
        g, _ = await get_or_create(session, UOM, name="g")
        litre, _ = await get_or_create(session, UOM, name="litre")
        piece, _ = await get_or_create(session, UOM, name="piece")

        # Create Taxes
        gst_5, _ = await get_or_create(session, Tax, name="GST 5%", rate=5.0)
        gst_12, _ = await get_or_create(session, Tax, name="GST 12%", rate=12.0)
        gst_18, _ = await get_or_create(session, Tax, name="GST 18%", rate=18.0)

        # Create Locations
        blr, _ = await get_or_create(session, Location, name="Bangalore", pincode="560001")
        mum, _ = await get_or_create(session, Location, name="Mumbai", pincode="400001")

        # Create Platforms
        platforms = []
        for name in ["Blinkit", "Zepto", "Instamart", "BigBasket Now", "Swiggy Instamart"]:
            platform, _ = await get_or_create(session, Platform, name=name, base_url=f"https://{name.lower()}.com")
            platforms.append(platform)

        # Create Categories and Brands
        categories = [await get_or_create(session, Category, name=fake.word()) for _ in range(20)]
        brands = [await get_or_create(session, Brand, name=fake.company()) for _ in range(50)]

        # Create Products
        for i in range(10000):
            product = Product(
                name=fake.ecommerce_name(),
                description=fake.text(),
                category=random.choice(categories)[0],
                brand=random.choice(brands)[0],
            )
            session.add(product)
            await session.flush()

            # Create initial price and availability for each platform
            for platform in platforms:
                price = ProductPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    price=random.uniform(10.0, 500.0),
                    currency_id=inr.id,
                )
                availability = ProductAvailability(
                    product_id=product.id,
                    platform_id=platform.id,
                    is_available=random.choice([True, False]),
                )
                session.add_all([price, availability])
        
        await session.commit()

async def get_or_create(session: AsyncSession, model, **kwargs):
    instance = await session.execute(
        model.__table__.select().where(
            *[getattr(model, k) == v for k, v in kwargs.items()]
        )
    )
    instance = instance.scalars().first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        await session.commit()
        return instance, True

if __name__ == "__main__":
    asyncio.run(seed_data()) 