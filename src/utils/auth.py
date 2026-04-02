import os
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.getenv("CLIFO_API_KEY")
    
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing environmental variables"
        )
        
    if api_key == expected_api_key:
        return api_key
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="Access denied"
    )
