from core.crypto import encrypt_data


class MessageSerializer:

    @staticmethod
    def serialize(data) -> bytes:

        return encrypt_data(data).encode()