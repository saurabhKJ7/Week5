# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.product import *  # noqa
from app.models.platform import *  # noqa
from app.models.misc import *  # noqa 