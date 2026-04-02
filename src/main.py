import uvicorn
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from database.connection import execute_query
from utils.validator import is_valid_cnpj

app = FastAPI(title="CliFo API", description="API for simplified customer and supplier registration in Totvs RM")

class RegisterRequest(BaseModel):
    cnpj_type: str
    cnpj: str
    ie: Optional[str] = ""

@app.post("/register")
def register_cnpj(request: RegisterRequest):
    try:
        valid_types = ['C', 'F', 'A']
        clean_type = request.cnpj_type.upper().strip()
        if clean_type not in valid_types:
            raise ValueError(f"Invalid CNPJ type. Must be one of: {valid_types}")

        clean_cnpj = re.sub(r'\D', '', request.cnpj)
        if not is_valid_cnpj(clean_cnpj):
            raise ValueError("Invalid CNPJ")

        if request.ie and 'isento' in request.ie.strip().lower():
            clean_ie = 'isento'
        else:
            clean_ie = re.sub(r'\D', '', request.ie) if request.ie else ""

        formatted_cnpj = f"{clean_cnpj[:2]}.{clean_cnpj[2:5]}.{clean_cnpj[5:8]}/{clean_cnpj[8:12]}-{clean_cnpj[12:]}"
        query = f"SELECT TOP 1 CODCFO FROM FCFO WHERE CODCOLIGADA IN (1,5,6) AND CGCCFO = '{formatted_cnpj}'"
        cnpj_exists = execute_query(query)
        if cnpj_exists:
            raise ValueError("CNPJ already registered in the system")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
