from apis.receitaws import cnpj_lookup
from apis.customer_vendor import register_new_customer_vendor


resp = cnpj_lookup(cnpj_type="F", cnpj="00.000.000/0000-00", ie="0000000000")

for idx in ["1", "2", "3"]:
    print (
        register_new_customer_vendor(
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
    )
