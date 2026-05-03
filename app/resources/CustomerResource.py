from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService


class Customer(BaseModel):
    customerNumber: int | None = None
    customerName: str = ""
    contactLastName: str = ""
    contactFirstName: str = ""
    phone: str = ""
    addressLine1: str = ""
    addressLine2: str | None = None
    city: str = ""
    state: str | None = None
    postalCode: str | None = None
    country: str = ""
    salesRepEmployeeNumber: int | None = None
    creditLimit: Decimal | None = None


class CustomerCollection(BaseModel):
    items: list[Customer] = Field(default_factory=list)


class CustomerResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        self._service = MySQLDataService({
            **cfg,
            "table": "customers",
            "primary_key_field": "customerNumber",
        })

    def get(self, template: dict) -> CustomerCollection:
        rows = self._service.retrieveByTemplate(template)
        return CustomerCollection(items=[Customer.model_validate(r) for r in rows])

    def get_by_id(self, id: str) -> Customer:
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No customer with customerNumber {id!r}")
        return Customer.model_validate(row)

    def post(self, new_data: Customer) -> str:
        return self._service.create(new_data.model_dump(exclude_none=False))

    def put(self, character_id: str, new_data: Customer) -> int:
        data = new_data.model_dump()
        data["customerNumber"] = character_id
        return self._service.updateByPrimaryKey(character_id, data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(id)
