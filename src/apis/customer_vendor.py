import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from database.connection import execute_query


def register_new_customer_vendor(
        companyId: str,
        code: str,
        shortName: str,
        name: str,
        type: int,
        mainNIF: str,
        stateRegister: str,
        zipCode: str,
        streetType: str,
		streetName: str,
		number: str,
        complement: str,
		districtType: str,
		district: str,
		stateCode: str,
		cityInternalId: str,
		phoneNumber: str,
		email: str,
        contributor: int
):
    load_dotenv(override=True)

    api_url = os.getenv("API_URL")
    api_user = os.getenv("API_USER")
    api_user_pwd = os.getenv("API_USER_PWD")

    if not api_url or not api_user or not api_user_pwd:
        raise RuntimeError("Missing environmental variables")

    session = requests.Session()
    session.auth = HTTPBasicAuth(api_user, api_user_pwd)
    session.headers.update({"Accept": "application/json"})

    json = {
        "companyId": companyId,
        "code": code,
        "companyInternalId": f"{companyId}|{code}",
        "shortName": shortName,
        "name": name,
        "type": type,
        "entityType": "J",  # Pessoa jurídica
        "mainNIF": mainNIF,
        "stateRegister": stateRegister,
        "registerSituation": 1,  # Ativo
        "address": {
            "zipCode": zipCode,
            "streetType": streetType,
            "streetName": streetName,
            "number": number,
            "districtType": districtType,
            "district": district,
            "country": {
                "countryInternalId": "1",
                "countryDescription": "Brasil"
            },
            "state": {
                "stateCode": stateCode
            },
            "city": {
                "cityInternalId": cityInternalId
            },
            "communicationInformation": {
                "phoneNumber": phoneNumber,
                "email": email
            }
        },
        "contributor": contributor,
        "fuelOperationType": 3,  # Nenhum
        "complementaryFields": {
            "codcoligada": int(companyId),
            "codcfo": code
        }
    }

    try:
        resp = session.post(api_url, json=json, timeout=30)
        resp.raise_for_status()

        complement = "'" + complement.replace("'", "").replace('"', "") + "'" if complement else "Null"
        query = f"UPDATE FCFO SET CONTRIBUINTE = {contributor}, COMPLEMENTO = {complement} WHERE CODCOLIGADA = {companyId} AND CGCCFO = '{mainNIF}'"
        execute_query(query)

        return {"success": True, "message": "Registered successfully"}
    
    except requests.exceptions.HTTPError as e:
        error_detail = resp.text if resp else str(e)
        raise RuntimeError(f"Error in the RM API: {error_detail}")
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Communication failure with the RM API: {str(e)}")
    
    except Exception as e:
        raise RuntimeError(f"Internal error: {str(e)}")
