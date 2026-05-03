from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService


class OrderDetail(BaseModel):
    orderNumber: int | None = None
    productCode: str = ""
    quantityOrdered: int | None = None
    priceEach: Decimal | None = None
    orderLineNumber: int | None = None


class OrderDetailCollection(BaseModel):
    items: list[OrderDetail] = Field(default_factory=list)


class OrderDetailsResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        self._service = MySQLDataService({
            **cfg,
            "table": "orderdetails",
            "primary_key_field": "orderNumber",
        })

    def get(self, template: dict) -> OrderDetailCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderDetailCollection(items=[OrderDetail.model_validate(r) for r in rows])

    def get_by_id(self, order_number: str) -> OrderDetailCollection:
        """Return all detail rows for a given orderNumber."""
        rows = self._service.retrieveByTemplate({"orderNumber": order_number})
        return OrderDetailCollection(items=[OrderDetail.model_validate(r) for r in rows])

    def get_by_key(self, order_number: str, product_code: str) -> OrderDetail:
        """Return a single row identified by the composite primary key."""
        rows = self._service.retrieveByTemplate(
            {"orderNumber": order_number, "productCode": product_code}
        )
        if not rows:
            raise ValueError(
                f"No order detail with orderNumber {order_number!r} and productCode {product_code!r}"
            )
        return OrderDetail.model_validate(rows[0])

    def post(self, new_data: OrderDetail) -> str:
        return self._service.create(new_data.model_dump(exclude_none=False))

    def put(self, order_number: str, product_code: str, new_data: OrderDetail) -> int:
        """Update a single row by composite primary key."""
        rows = self._service.retrieveByTemplate(
            {"orderNumber": order_number, "productCode": product_code}
        )
        if not rows:
            raise ValueError(
                f"No order detail with orderNumber {order_number!r} and productCode {product_code!r}"
            )
        data = new_data.model_dump(exclude_none=False)
        # Build a targeted UPDATE using both key columns as the WHERE clause.
        import pymysql
        import pymysql.cursors
        update_data = {
            k: v for k, v in data.items()
            if k not in ("orderNumber", "productCode")
        }
        if not update_data:
            return 0
        assignments = ", ".join(f"`{k}` = %s" for k in update_data)
        sql = (
            f"UPDATE `orderdetails` SET {assignments} "
            f"WHERE `orderNumber` = %s AND `productCode` = %s"
        )
        params = (*update_data.values(), order_number, product_code)
        conn = self._service._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.rowcount
        finally:
            conn.close()

    def delete(self, order_number: str, product_code: str) -> int:
        """Delete a single row by composite primary key."""
        sql = (
            "DELETE FROM `orderdetails` "
            "WHERE `orderNumber` = %s AND `productCode` = %s"
        )
        conn = self._service._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (order_number, product_code))
                return cursor.rowcount
        finally:
            conn.close()
