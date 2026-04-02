import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from apis.receitaws import cnpj_lookup
from apis.customer_vendor import register_new_customer_vendor


app = FastAPI(title="CliFo API", description="API for simplified customer and supplier registration in Totvs RM")


class RegisterRequest(BaseModel):
    cnpj_type: str
    cnpj: str
    ie: Optional[str] = ""

@app.post("/register")
def register_cnpj(request: RegisterRequest):
    try:
        results = []
        
        resp = cnpj_lookup(cnpj_type=request.cnpj_type, cnpj=request.cnpj, ie=request.ie)
        
        for idx in ["1", "5", "6"]:
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
            
        return {
            "message": "Processing completed successfully", 
            "data": results
        }

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
