import uvicorn
import re
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database.connection import execute_query
from utils.validator import is_valid_cnpj
from apis.receitaws import cnpj_lookup
from apis.customer_vendor import register_new_customer_vendor
from utils.auth import get_api_key

app = FastAPI(title="CliFo API", description="API for simplified customer and supplier registration in Totvs RM")

class RegisterRequest(BaseModel):
    cnpj_type: str
    cnpj: str
    ie: Optional[str] = ""

@app.post("/register", dependencies=[Depends(get_api_key)])
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
            existing_code = cnpj_exists[0][0]
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": "CNPJ already registered in the system",
                    "codcfo": existing_code
                }
            )

        resp = cnpj_lookup(cnpj_type=clean_type, cnpj=clean_cnpj, ie=clean_ie)
        if resp.get("status", "").upper() != "ATIVA":
            raise ValueError(f"CNPJ is not active. Current status: {resp.get('status', 'UNKNOWN')}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    results = []
    errors = []
    
    for idx in ["1", "5", "6"]:
        try:
            result = register_new_customer_vendor(
                companyId=idx,
                code=resp["code"],
                shortName=resp["shortName"],
                name=resp["name"],
                type=resp["type"],
                mainNIF=resp["mainNIF"],
                stateRegister=resp["stateRegister"],
                zipCode=resp["zipCode"],
                streetType=resp["streetType"],
                streetName=resp["streetName"],
                number=resp["number"],
                complement=resp["complement"],
                districtType=resp["districtType"],
                district=resp["district"],
                stateCode=resp["stateCode"],
                cityInternalId=resp["cityInternalId"],
                phoneNumber=resp["phoneNumber"],
                email=resp["email"],
                contributor=resp["contributor"]
            )
            results.append({
                "companyId": idx,
                "status": "processed",
                "details": result
            })

        except Exception as e:
            errors.append({
                "companyId": idx,
                "status": "failed",
                "details": str(e)
            })
            
    return {
        "message": "Processing complete", 
        "codcfo": resp["code"],
        "successes": results,
        "failures": errors
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
