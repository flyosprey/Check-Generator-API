import datetime
import hashlib
import hmac

from sqlalchemy import asc
from sqlalchemy.orm import joinedload

import models
from config import Config
from utils.exceptions import bad_request_exception


def generate_signature(check_id) -> str:
    return hmac.new(
        Config.SECRET_KEY.encode(), str(check_id).encode(), hashlib.sha256
    ).hexdigest()


def generate_check_url(url_obj, check_id: int) -> str:
    signature = generate_signature(check_id=check_id)
    url = f"http://{url_obj.hostname}:{url_obj.port}/checks/{check_id}/{signature}/"

    return url


def serialize_check(url_obj, check: models.Checks) -> dict:
    return {
        "check_id": check.id,
        "payment_type": check.payment_type,
        "payment_amount": check.payment_amount,
        "total": check.total,
        "rest": check.rest,
        "comment": check.comment,
        "buyer_name": check.buyer_name,
        "created_at": check.created_at,
        "url": generate_check_url(url_obj=url_obj, check_id=check.id),
        "products": [
            {
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": product.quantity,
                "total": product.total,
            }
            for product in check.products
        ],
    }


async def get_filtered_checks(filters: dict, user_id: int, url, db) -> dict:
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    query = (
        db.query(models.Checks)
        .filter(models.Checks.owner == user)
        .options(joinedload(models.Checks.products))
    )

    if filters["total_from"]:
        query = query.filter(models.Checks.total >= float(filters["total_from"]))
    if filters["payment_type"]:
        query = query.filter(models.Checks.payment_type == filters["payment_type"])
    if filters["date_from"]:
        date_from = datetime.datetime.strptime(filters["date_from"], "%d/%m/%Y")
        query = query.filter(models.Checks.created_at >= date_from)

    query = query.order_by(asc(models.Checks.created_at))
    query = query.offset(filters["per_page"] * (filters["page"] - 1)).limit(
        filters["per_page"] * filters["page"]
    )

    response_data = {
        "total_count": query.count(),
        "checks": [serialize_check(url, check) for check in query.all()],
    }

    return response_data


async def add_check_to_db(order, user_id: int, db) -> dict:
    total = sum([product.price * product.quantity for product in order.products])
    if total > order.payment.amount:
        raise bad_request_exception(
            detail="Payment amount cannot be less than total product's cost"
        )

    check_model = models.Checks()
    check_model.created_at = datetime.datetime.utcnow()
    check_model.payment_amount = order.payment.amount
    check_model.rest = order.payment.amount - total
    check_model.payment_type = order.payment.type
    check_model.comment = order.comment
    check_model.user_id = user_id
    check_model.total = total
    check_model.buyer_name = order.buyer_name
    db.add(check_model)
    db.flush()

    product_models, products = [], []
    for product in order.products:
        total_price = product.price * product.quantity
        products.append({**product.__dict__, "total": total_price})
        product_models.append(
            models.Products(
                name=product.name,
                check_id=check_model.id,
                price=product.price,
                quantity=product.quantity,
                total=total_price,
            )
        )

    db.bulk_save_objects(product_models)
    db.commit()

    response = {
        "id": check_model.id,
        "products": products,
        "payment": {
            "amount": check_model.payment_amount,
            "type": check_model.payment_type,
        },
        "total": check_model.total,
        "rest": check_model.rest,
        "created_at": check_model.created_at,
        "buyer_name": check_model.buyer_name,
    }

    return response


async def get_check_by_id(check_id: str, db):
    return (
        db.query(models.Checks)
        .filter(models.Checks.id == check_id)
        .options(joinedload(models.Checks.products))
    ).first()
