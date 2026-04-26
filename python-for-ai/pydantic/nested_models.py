from pydantic import BaseModel, EmailStr


class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    price: float


class Order(BaseModel):
    order_id: str
    customer_email: EmailStr
    items: list[OrderItem]


order = Order(
    order_id="ORD-001",
    customer_email="customer@example.com",
    items=[OrderItem(product_id="P1", name="Widget", quantity=2, price=29.99)],
)

api_response = {
    "order_id": "ORD-001",
    "customer_email": "customer@example.com",
    "items": [
        {"product_id": "P1", "name": "Widget", "quantity": 2, "price": 29.99},
        {"product_id": "P2", "name": "Gadget", "quantity": 1, "price": 49.99},
    ],
}

order = Order(**api_response)

print(f"Order {order.order_id}")
for item in order.items:
    print(f"  - {item.name}: {item.quantity} x ${item.price}")
