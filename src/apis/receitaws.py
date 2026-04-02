import requests
from database.connection import execute_query
from utils.formatter import (
    format_name, 
    suffix_remover, 
    format_zipcode, 
    format_street, 
    format_number,
    format_district, 
    format_municipality, 
    format_phone
)


def cnpj_lookup(cnpj_type: str, cnpj: str, ie: str = ""):
    r = requests.get(f"https://receitaws.com.br/v1/cnpj/{cnpj}", timeout=30)
    r.raise_for_status()
    resp = r.json()

    if isinstance(resp, dict) and resp.get("status") == "ERROR":
        raise RuntimeError(resp.get("message"))

    codes = execute_query("""
        SELECT
            'F' + RIGHT('00000' + CAST((CAST(SUBSTRING((SELECT TOP 1 CODCFO FROM FCFO WHERE CODCFO LIKE 'F%' AND CODCOLIGADA in (1,5,6) ORDER BY CODCFO DESC), 2, 5) AS INT) + 1) AS VARCHAR), 5),
            'C' + RIGHT('00000' + CAST((CAST(SUBSTRING((SELECT TOP 1 CODCFO FROM FCFO WHERE CODCFO LIKE 'C%' AND CODCOLIGADA in (1,5,6) ORDER BY CODCFO DESC), 2, 5) AS INT) + 1) AS VARCHAR), 5)
    """)[0]
    codcfo = codes[1] if cnpj_type.upper() == "C" else codes[0]

    response = {
        "status": resp["situacao"].title(),
        "code": codcfo,
        "shortName": suffix_remover(format_name(resp["fantasia"])) if resp["fantasia"] else suffix_remover(format_name(resp["nome"])),
        "name": format_name(resp["nome"]),
        "type": 1 if cnpj_type.upper() == 'C' else (2 if cnpj_type.upper() == 'F' else 3),  # 1 = Cliente | 2 = Fornecedor | 3 = Ambos
        "mainNIF": resp["cnpj"].strip(),
        "stateRegister": ie if ie and "isento" not in ie.lower() else "",
        "zipCode": format_zipcode(resp["cep"]),
        "streetType": format_street(resp["logradouro"])[0],
        "streetName": format_street(resp["logradouro"])[1],
        "number": format_number(resp["numero"]),
        "complement": resp["complemento"].title().strip(),
        "districtType": format_district(resp["bairro"])[0],
        "district": format_district(resp["bairro"])[1],
        "stateCode": resp["uf"].upper().strip(),
        "cityInternalId": format_municipality(resp["municipio"], resp["uf"]),
        "phoneNumber": format_phone(resp["telefone"]),
        "email": resp["email"].lower().strip(),
        "contributor": 2 if ie and "isento" in ie.lower() else (1 if ie else 0)  # 0 = Não contribuinte | 1 = Contribuinte | 2 = Isento
    }

    return response
