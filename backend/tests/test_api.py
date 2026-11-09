import os

os.environ["DATABASE_URL"] = "sqlite:///./tmp/pytest.db"

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from backend.app.database import Base, SessionLocal, engine
from backend.app.main import advance_order, create_order, dashboard, seed
from backend.app.models import Resource
from backend.app.schemas import AdvanceRequest, ConsumptionCreate, OrderCreate


def setup_module():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


def test_manufacturing_flow():
    with SessionLocal() as db:
        assert dashboard(db).active_orders == 4
        order = create_order(OrderCreate(
            product="Mandibular Implant", customer="Test Hospital", quantity=6, priority="high"
        ), db)
        assert order.current_step.name == "Material Prep"
        assert len(order.history) == 1

        resource_id = db.scalar(select(Resource.id))
        moved = advance_order(order.id, AdvanceRequest(consumptions=[
            ConsumptionCreate(resource_id=resource_id, amount=2.5)
        ]), db)
        assert moved.current_step.name == "Machining"
        assert float(moved.consumptions[0].amount) == 2.5
        assert moved.history[0].exited_at is not None


def test_rejects_invalid_order():
    with pytest.raises(ValidationError):
        OrderCreate(product="X", customer="Y", quantity=0, priority="low")
