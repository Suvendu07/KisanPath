from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from fastapi import Request



access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")




def hash_password(password : str) -> str:
    
    return pwd_context.hash(password)





def verify_password(plain_password:str, hash_password: str) -> bool:
    
    return pwd_context.verify(plain_password, hash_password)



def create_access_token(data : dict, expire_delta : Optional[timedelta] = None) -> str:
    
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (expire_delta if expire_delta
                                  else timedelta(minutes = access_token_expire))
    
    to_encode.update({
        "exp" : expire,
        "type" : "access"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



def create_refresh_token(data : dict) -> str:
    
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp" : expire,
        "type" : "refresh"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token : str) -> Optional[dict]:
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        
        return payload
    
    except JWTError:
        return None