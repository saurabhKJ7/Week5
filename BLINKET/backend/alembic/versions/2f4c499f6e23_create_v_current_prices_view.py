"""Create v_current_prices view

Revision ID: 2f4c499f6e23
Revises: 5c57a4af0f67
Create Date: 2024-08-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f4c499f6e23'
down_revision: Union[str, None] = '5c57a4af0f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE VIEW v_current_prices AS
    SELECT
        p.id          AS product_id,
        p.name        AS product_name,
        p.description AS product_description,
        c.name        AS category_name,
        b.name        AS brand_name,
        plt.name      AS platform_name,
        pr.price,
        cur.code      AS currency,
        pr.timestamp
    FROM   products p
    JOIN   product_prices pr ON pr.product_id = p.id
    JOIN   platforms plt ON pr.platform_id = plt.id
    JOIN   currencies cur ON pr.currency_id = cur.id
    JOIN   categories c ON p.category_id = c.id
    JOIN   brands b ON p.brand_id = b.id
    WHERE  pr.timestamp = (
            SELECT MAX(pr2.timestamp)
            FROM   product_prices pr2
            WHERE  pr2.product_id = p.id
              AND  pr2.platform_id = pr.platform_id
    )
    """)


def downgrade() -> None:
    op.execute("DROP VIEW v_current_prices")
