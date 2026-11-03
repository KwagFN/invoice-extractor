from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = Field(description="What was sold, as written on the invoice")
    quantity: Decimal = Field(gt=0, description="Number of units")
    unit_price: Decimal = Field(ge=0, description="Price of one unit")
    amount: Decimal = Field(ge=0, description="Line total as printed on the invoice")


class Invoice(BaseModel):
    invoice_number: str = Field(description="Invoice number or ID")
    issue_date: date = Field(description="Date the invoice was issued (YYYY-MM-DD)")
    vendor_name: str = Field(description="Company that issued the invoice")
    customer_name: str = Field(description="Company or person being billed")
    currency: str = Field(
        min_length=3, max_length=3, description="ISO 4217 code, e.g. USD, EUR, BRL"
    )
    line_items: list[LineItem]
    subtotal: Decimal = Field(description="Sum of line items before tax")
    tax: Decimal = Field(default=Decimal("0"), description="Total tax, 0 if none")
    total: Decimal = Field(description="Amount due, as printed on the invoice")
