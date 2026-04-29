import os
import jwt
from datetime import datetime, timedelta, timezone

from app.organizer import schemas,database,models
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/organizerLogin")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Customer portal sessions (browsing + checkout) are longer than organizer form login.
CUSTOMER_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("CUSTOMER_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


def verify_access_token(token:str, credential_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id: str = payload.get("user_id")

        if id is None:
            raise credential_exception
        token_data = schemas.TokenData(id=id)
    
    except InvalidTokenError:
        raise credential_exception
    
    return token_data

# def get_current_user(token:str = Depends(oauth2_scheme), db:Session=Depends(database.get_db)):
#         credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#         )

#         token = verify_access_token(token, credentials_exception)
#         user = db.query(models.OrganizerInfo).filter(models.OrganizerInfo.org_id==token.id).first()
#         return user



from fastapi import Request

def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    # 1. Manually get the token from the cookie
    token_cookie = request.cookies.get("access_token")
    
    if not token_cookie or not token_cookie.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authorized - No Cookie Found")
    
    # 2. Strip "Bearer " to get the actual JWT string
    token = token_cookie.split(" ")[1]
    
    # 3. Use your existing verification logic
    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials"
    )

    token_data = verify_access_token(token, credentials_exception)
    
    # 4. Fetch the user
    user = db.query(models.OrganizerInfo).filter(models.OrganizerInfo.org_id == token_data.id).first()
    if user is None:
        raise credentials_exception
    return user