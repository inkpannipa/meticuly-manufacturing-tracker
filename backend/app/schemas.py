from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    sequence: int
    color: str


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    unit: str
    capacity: Decimal


class ConsumptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    recorded_at: datetime
    resource: ResourceOut
    step: StepOut


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entered_at: datetime
    exited_at: datetime | None
    step: StepOut


class OrderCreate(BaseModel):
    product: str = Field(min_length=2, max_length=120)
    customer: str = Field(min_length=2, max_length=120)
    quantity: int = Field(gt=0, le=1_000_000)
    priority: str = Field(pattern="^(normal|high|urgent)$")


class ConsumptionCreate(BaseModel):
    resource_id: int
    amount: Decimal = Field(gt=0)


class AdvanceRequest(BaseModel):
    consumptions: list[ConsumptionCreate] = []


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    product: str
    customer: str
    quantity: int
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    current_step: StepOut | None
    history: list[HistoryOut] = []
    consumptions: list[ConsumptionOut] = []


class DashboardOut(BaseModel):
    total_orders: int
    active_orders: int
    completed_orders: int
    urgent_orders: int
    by_step: list[dict]
    resource_usage: list[dict]

