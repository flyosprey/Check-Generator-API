from fastapi import Depends, APIRouter, Request, Query, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import constr

from schemas.check_schema import Order
from utils.utils import get_db
from utils.exceptions import bad_request_exception, not_found_exception, get_user_exception
from services.check_service import get_filtered_checks, add_check_to_db, generate_signature, get_check_by_id
from services.auth_service import get_current_user


router = APIRouter(
    prefix="/checks",
    tags=["checks"],
    responses={404: {"description": "Not found"}}
)

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

    filters = {
        "page": page,
        "per_page": per_page,
        "total_from": total_from,
        "date_from": date_from,
        "payment_type": payment_type
    }

    filtered_checks = get_filtered_checks(filters=filters, user_id=user["id"], url=request.url, db=db)

    return filtered_checks


@router.get("/{check_id}/{signature}/", status_code=status.HTTP_200_OK)
async def view_check(request: Request, check_id: str, signature: str, db: Session = Depends(get_db)):

    expected_signature = generate_signature(check_id=check_id)
    if signature != expected_signature:
        raise bad_request_exception(detail="Invalid signature")

    check = get_check_by_id(check_id=check_id, db=db)
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

    response = add_check_to_db(order=order, user_id=user["id"], db=db)

    return response
