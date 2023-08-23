import datetime

from fastapi import (
    Depends, APIRouter, Request, Query, FastAPI, status
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc
from pydantic import constr

import models
from database import engine
from schemas.check import Order
from utils.exceptions import bad_request_exception, not_found_exception
from utils.utils import get_db
from .auth import get_current_user, get_user_exception


router = APIRouter(
    prefix="/checks",
    tags=["checks"],
    responses={404: {"description": "Not found"}}
)

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(
        request: Request,
        db: Session = Depends(get_db),
        user: dict = Depends(get_current_user),
        page: int = Query(default=1, description="Page number"),
        per_page: int = Query(default=5, description="Records per page"),
        total_from: constr(regex=r"^\d*([.,]\d*)?$") = Query(default=0, description="Minimal price"),
        date_from: constr(regex=r"^\d{2}/\d{2}/\d{4}$") = Query(default="", description="DD/MM/YYYY"),
        payment_type: constr(regex=r"^cash(less)?$") = Query(default="", description="'cash' or 'cashless'"),
):
    if user is None:
        raise get_user_exception()

    user = db.query(models.Users).filter(models.Users.id == user["id"]).first()
    query = (db.query(models.Checks).filter(models.Checks.owner == user).options(joinedload(models.Checks.products)))

    if total_from:
        query = query.filter(models.Checks.total >= float(total_from))
    if payment_type:
        query = query.filter(models.Checks.payment_type == payment_type)
    if date_from:
        date_from = datetime.datetime.strptime(date_from, "%d/%m/%Y")
        query = query.filter(models.Checks.created_at >= date_from)

    query = query.order_by(asc(models.Checks.created_at))
    query = query.offset(per_page * (page - 1)).limit(per_page * page)

    response_data = {
        "total_count": query.count(),
        "checks": [
            serialize_check(request.url, check)
            for check in query.all()
        ]
    }

    return response_data


@router.get("/{check_id}/", status_code=status.HTTP_200_OK)
async def view_check(request: Request, check_id: str, db: Session = Depends(get_db)):
    check = (
        db.query(models.Checks)
        .filter(models.Checks.id == check_id)
        .options(joinedload(models.Checks.products))
    ).first()

    if not check:
        raise not_found_exception(detail="Check not found")

    return templates.TemplateResponse(
        "check/check.html",
        {"request": request, "check": check}
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_check(order: Order, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    total = sum([product.price * product.quantity for product in order.products])
    if total > order.payment.amount:
        raise bad_request_exception(detail="Payment amount cannot be less than total product's cost")

    with db.begin():
        check_model = models.Checks()
        check_model.created_at = datetime.datetime.utcnow()
        check_model.payment_amount = order.payment.amount
        check_model.rest = order.payment.amount - total
        check_model.payment_type = order.payment.type
        check_model.comment = order.comment
        check_model.user_id = user["id"]
        check_model.total = total
        check_model.buyer_name = order.buyer_name
        db.add(check_model)
        db.flush()

        product_models, products = [], []
        for product in order.products:
            total_price = product.price * product.quantity
            products.append({**product.__dict__, "total": total_price})
            product_models.append(models.Products(name=product.name, check_id=check_model.id, price=product.price,
                                                  quantity=product.quantity, total=total_price))

        db.bulk_save_objects(product_models)
        db.commit()

    response = {
        "id": check_model.id,
        "products": products,
        "payment": {
            "amount": check_model.payment_amount,
            "type": check_model.payment_type
        },
        "total": check_model.total,
        "rest": check_model.rest,
        "created_at": check_model.created_at,
        "buyer_name": check_model.buyer_name
    }

    return response


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
        "url": f"http://{url_obj.hostname}:{url_obj.port}/checks/{check.id}/",
        "products": [
            {
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": product.quantity,
                "total": product.total
            }
            for product in check.products
        ]
    }
