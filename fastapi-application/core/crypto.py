import json
import hashlib
import hmac
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from core.config import settings

load_dotenv()

SECRET_KEY = settings.cryptography.db_encryption_key
PASSPORT_HASH_SALT = settings.cryptography.passport_hash_salt.encode()
CARD_HASH_SALT = settings.cryptography.card_hash_salt.encode()
cipher = Fernet(SECRET_KEY)

def encrypt_data(data):
    json_data = json.dumps(data).encode()
    return cipher.encrypt(json_data).decode()

def decrypt_data(encrypted_text):
    decrypted_data = cipher.decrypt(encrypted_text)
    return json.loads(decrypted_data)

def generate_passport_search_hash(passport_number):
    return hmac.new(
        PASSPORT_HASH_SALT,
        passport_number.strip().encode(),
        hashlib.sha256
    ).hexdigest()

def generate_card_search_hash(card_number):
    return hmac.new(
        CARD_HASH_SALT,
        card_number.strip().encode(),
        hashlib.sha256
    ).hexdigest()


