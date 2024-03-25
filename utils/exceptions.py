from fastapi import HTTPException, status


def not_found_exception(detail):
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request_exception(detail):
    return HTTPException(status_code=400, detail=detail)


def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    return credentials_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    return token_exception_response
