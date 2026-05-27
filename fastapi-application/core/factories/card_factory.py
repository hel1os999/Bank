from core.config import settings

import random


class UniqueRandomGenerator:
    def __init__(self):
        self.used = set()

    def generate(self, account_id: int) -> str:
        account_id_str = str(account_id)
        account_id_len = len(account_id_str)

        if account_id_len > 8:
            raise ValueError("Account ID too long")

        prefix_len = 8 - account_id_len

        while True:
            prefix = ''.join(str(random.randint(0, 9)) for _ in range(prefix_len))
            result = prefix + account_id_str

            if result not in self.used:
                self.used.add(result)
                return result

    def reset(self):
        self.used.clear()



def create_card_number(card_type: str, account_id) -> str:
    for_card = []

    chase_bank = str(settings.card_variable.chase_bin)
    sparkasse_bank = str(settings.card_variable.sparkasse_bin)

    gen = UniqueRandomGenerator()

    eight_digits = gen.generate(account_id)

    if card_type == "VISA":
        mid = len(chase_bank) // 2
        first = chase_bank[:mid]
        one_part = str(4) + first
        for_card.append(one_part)

    else:
        mid = len(sparkasse_bank) // 2
        first = sparkasse_bank[:mid]
        one_part = str(5) + first
        for_card.append(one_part)

    if for_card[0] == "4":
        mid = len(chase_bank) // 2
        second = chase_bank[mid:]
        two_part = second + eight_digits[0]
        for_card.append(two_part)

    else:
        mid = len(sparkasse_bank) // 2
        second = sparkasse_bank[mid:]
        two_part = second + eight_digits[0]
        for_card.append(two_part)

    seven_digits = eight_digits[1:]
    mid = len(seven_digits) // 2
    third_part = seven_digits[mid:]
    for_card.append(third_part)

    fourth_part = seven_digits[:mid] + str(random.randint(1,9))
    for_card.append(fourth_part)


    card_number = " ".join(for_card)

    return card_number







