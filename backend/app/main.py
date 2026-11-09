from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .database import Base, SessionLocal, engine, get_db
from .models import Consumption, Order, OrderHistory, Resource, Step
from .schemas import AdvanceRequest, DashboardOut, OrderCreate, OrderOut, ResourceOut, StepOut


def seed(db: Session) -> None:
    if not db.scalar(select(func.count(Step.id))):
        db.add_all([
            Step(name="Material Prep", sequence=1, color="#1f8f78"),
            Step(name="Machining", sequence=2, color="#3b71ca"),
            Step(name="Quality Check", sequence=3, color="#f0a43a"),
            Step(name="Packaging", sequence=4, color="#8b5cf6"),
        ])
    if not db.scalar(select(func.count(Resource.id))):
        db.add_all([
            Resource(name="Titanium", unit="kg", capacity=500),
            Resource(name="Machine Time", unit="hours", capacity=160),
            Resource(name="Labour", unit="hours", capacity=320),
            Resource(name="Packaging", unit="sets", capacity=1000),
        ])
    db.commit()

    if not db.scalar(select(func.count(Order.id))):
        steps = db.scalars(select(Step).order_by(Step.sequence)).all()
        samples = [
            ("Cranial Plate", "Bangkok General", 24, "urgent", 1),
            ("Patient Implant", "Medica Lab", 12, "high", 2),
            ("Bone Screw Kit", "Nova Surgical", 80, "normal", 0),
            ("Orbital Mesh", "Siam Health", 18, "normal", 3),
        ]
        for index, (product, customer, qty, priority, step_idx) in enumerate(samples, 1):
            order = Order(code=f"WO-2026-{index:03d}", product=product, customer=customer,
                          quantity=qty, priority=priority, current_step=steps[step_idx])
            db.add(order)
            db.flush()
            for step in steps[: step_idx + 1]:
                db.add(OrderHistory(order_id=order.id, step_id=step.id,
                                    exited_at=None if step.id == steps[step_idx].id else datetime.now(timezone.utc)))
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Meticuly Flow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


def order_query():
    return select(Order).options(
        selectinload(Order.current_step),
        selectinload(Order.history).selectinload(OrderHistory.step),
        selectinload(Order.consumptions).selectinload(Consumption.resource),
        selectinload(Order.consumptions).selectinload(Consumption.step),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/steps", response_model=list[StepOut])
def list_steps(db: Session = Depends(get_db)):
    return db.scalars(select(Step).order_by(Step.sequence)).all()


@app.get("/api/resources", response_model=list[ResourceOut])
def list_resources(db: Session = Depends(get_db)):
    return db.scalars(select(Resource).order_by(Resource.id)).all()


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(state: str | None = Query(None), db: Session = Depends(get_db)):
    stmt = order_query().order_by(Order.created_at.desc())
    if state:
        stmt = stmt.where(Order.status == state)
    return db.scalars(stmt).unique().all()


@app.post("/api/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    first_step = db.scalar(select(Step).order_by(Step.sequence).limit(1))
    if not first_step:
        raise HTTPException(500, "Workflow is not configured")
    year = datetime.now().year
    count = db.scalar(select(func.count(Order.id))) or 0
    code = f"WO-{year}-{count + 1:03d}"
    order = Order(code=code, current_step_id=first_step.id, **payload.model_dump())
    db.add(order)
    db.flush()
    db.add(OrderHistory(order_id=order.id, step_id=first_step.id))
    db.commit()
    db.expire_all()
    return db.scalar(order_query().where(Order.id == order.id))


@app.post("/api/orders/{order_id}/advance", response_model=OrderOut)
def advance_order(order_id: int, payload: AdvanceRequest, db: Session = Depends(get_db)):
    order = db.scalar(order_query().where(Order.id == order_id))
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status == "completed" or not order.current_step:
        raise HTTPException(409, "Order is already completed")

    resource_ids = {item.resource_id for item in payload.consumptions}
    resources = db.scalars(select(Resource).where(Resource.id.in_(resource_ids))).all() if resource_ids else []
    if len(resources) != len(resource_ids):
        raise HTTPException(422, "One or more resources do not exist")
    for item in payload.consumptions:
        db.add(Consumption(order_id=order.id, step_id=order.current_step.id,
                           resource_id=item.resource_id, amount=item.amount))

    open_history = db.scalar(select(OrderHistory).where(
        OrderHistory.order_id == order.id, OrderHistory.exited_at.is_(None)))
    if open_history:
        open_history.exited_at = datetime.now(timezone.utc)

    next_step = db.scalar(select(Step).where(Step.sequence > order.current_step.sequence)
                          .order_by(Step.sequence).limit(1))
    if next_step:
        order.current_step_id = next_step.id
        db.add(OrderHistory(order_id=order.id, step_id=next_step.id))
    else:
        order.current_step_id = None
        order.status = "completed"
    db.commit()
    db.expire_all()
    return db.scalar(order_query().where(Order.id == order.id))


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    steps = db.scalars(select(Step).order_by(Step.sequence)).all()
    resources = db.scalars(select(Resource).order_by(Resource.id)).all()
    by_step = [{"step": s.name, "color": s.color,
                "count": db.scalar(select(func.count(Order.id)).where(Order.current_step_id == s.id)) or 0}
               for s in steps]
    resource_usage = []
    for resource in resources:
        used = db.scalar(select(func.coalesce(func.sum(Consumption.amount), 0))
                         .where(Consumption.resource_id == resource.id))
        resource_usage.append({"name": resource.name, "unit": resource.unit, "used": float(used),
                               "capacity": float(resource.capacity)})
    return DashboardOut(
        total_orders=db.scalar(select(func.count(Order.id))) or 0,
        active_orders=db.scalar(select(func.count(Order.id)).where(Order.status == "active")) or 0,
        completed_orders=db.scalar(select(func.count(Order.id)).where(Order.status == "completed")) or 0,
        urgent_orders=db.scalar(select(func.count(Order.id)).where(Order.priority == "urgent", Order.status == "active")) or 0,
        by_step=by_step, resource_usage=resource_usage,
    )

