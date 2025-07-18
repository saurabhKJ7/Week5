import asyncio
import random
import logging
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import SessionLocal
from app.models import Product, Platform, ProductPrice, ProductAvailability

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_price_updates():
    async with SessionLocal() as session:
        # Get all products and platforms
        products = (await session.execute(select(Product))).scalars().all()
        platforms = (await session.execute(select(Platform))).scalars().all()

        if not products or not platforms:
            logger.warning("No products or platforms found in the database. Skipping simulation.")
            return

        # Select a random subset of products to update
        products_to_update = random.sample(products, k=min(100, len(products)))

        for product in products_to_update:
            for platform in platforms:
                # Simulate price change
                new_price = round(random.uniform(product.prices[-1].price * 0.9, product.prices[-1].price * 1.1), 2)
                price_update = ProductPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    price=new_price,
                    currency_id=product.prices[-1].currency_id
                )

                # Simulate availability change
                new_availability = random.choice([True, False])
                availability_update = ProductAvailability(
                    product_id=product.id,
                    platform_id=platform.id,
                    is_available=new_availability
                )
                
                session.add_all([price_update, availability_update])
        
        await session.commit()
        logger.info(f"Simulated updates for {len(products_to_update)} products.")

if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    scheduler.add_job(simulate_price_updates, 'interval', seconds=30)
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass 