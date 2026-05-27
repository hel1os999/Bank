import random


def create_iban(user_id: str):

    letters = {
        "D": "13",
        "E" : "14"
    }

    for_iban_like = []

    num = random.randint(100000, 999999)

    bank_id = "11"
    bank_code = bank_id + str(num)

    account_number = user_id.zfill(10)

    for_iban_like.append(bank_code)
    for_iban_like.append(account_number)

    iban_like = "".join(for_iban_like) + letters["D"] + letters["E"] + "0" + "0"

    result = 98 - int(iban_like) % 97

    for_iban = []

    for_iban.append("DE")
    for_iban.append(str(result))
    for_iban.append(bank_code)
    for_iban.append(account_number)
    IBAN = " ".join(for_iban)
    return IBAN

