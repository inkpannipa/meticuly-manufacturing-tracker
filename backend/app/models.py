from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Step(Base):
    __tablename__ = "steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    sequence: Mapped[int] = mapped_column(Integer, unique=True)
    color: Mapped[str] = mapped_column(String(16))


class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    unit: Mapped[str] = mapped_column(String(24))
    capacity: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    product: Mapped[str] = mapped_column(String(120))
    customer: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="active")
    current_step_id: Mapped[int | None] = mapped_column(ForeignKey("steps.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    current_step: Mapped[Step | None] = relationship()
    history: Mapped[list["OrderHistory"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    consumptions: Mapped[list["Consumption"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderHistory(Base):
    __tablename__ = "order_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id"))
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="history")
    step: Mapped[Step] = relationship()


class Consumption(Base):
    __tablename__ = "consumptions"
    __table_args__ = (UniqueConstraint("order_id", "step_id", "resource_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id"))
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="consumptions")
    step: Mapped[Step] = relationship()
    resource: Mapped[Resource] = relationship()

