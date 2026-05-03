from __future__ import annotations

import datetime

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService


class Order(BaseModel):
    orderNumber: int | None = None
    orderDate: datetime.date | None = None
    requiredDate: datetime.date | None = None
    shippedDate: datetime.date | None = None
    status: str = ""
    comments: str | None = None
    customerNumber: int | None = None


class OrderCollection(BaseModel):
    items: list[Order] = Field(default_factory=list)


class OrderResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        self._service = MySQLDataService({
            **cfg,
            "table": "orders",
            "primary_key_field": "orderNumber",
        })

    def get(self, template: dict) -> OrderCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderCollection(items=[Order.model_validate(r) for r in rows])

    def get_by_id(self, id: str) -> Order:
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No order with orderNumber {id!r}")
        return Order.model_validate(row)

    def post(self, new_data: Order) -> str:
        return self._service.create(new_data.model_dump(exclude_none=False))

    def put(self, order_id: str, new_data: Order) -> int:
        data = new_data.model_dump()
        data["orderNumber"] = order_id
        return self._service.updateByPrimaryKey(order_id, data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(id)
