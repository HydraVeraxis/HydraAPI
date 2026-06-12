from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64

SALT_SIZE = 16
KEY_SIZE = 32   # AES-256
NONCE_SIZE = 16 # AES-GCM default; make this explicit
TAG_SIZE = 16   # AES-GCM tag is always 16 bytes
ITERATIONS = 100_000

def encrypt(text: str, password: str) -> str:
    salt = get_random_bytes(SALT_SIZE)

    key = PBKDF2(password, salt, dkLen=KEY_SIZE, count=ITERATIONS)

    cipher = AES.new(key, AES.MODE_GCM, mac_len=TAG_SIZE)
    ciphertext, tag = cipher.encrypt_and_digest(text.encode("utf-8"))

    data = salt + cipher.nonce + tag + ciphertext
    return base64.b64encode(data).decode("ascii")


def decrypt(encrypted_text: str, password: str) -> str:
    data = base64.b64decode(encrypted_text)

    salt  = data[:SALT_SIZE]
    nonce = data[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    tag   = data[SALT_SIZE + NONCE_SIZE : SALT_SIZE + NONCE_SIZE + TAG_SIZE]
    ciphertext = data[SALT_SIZE + NONCE_SIZE + TAG_SIZE:]

    key = PBKDF2(password, salt, dkLen=KEY_SIZE, count=ITERATIONS)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8")
