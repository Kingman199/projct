import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class Encryption:
    def __init__(self):
        # Define a valid AES key (16 bytes for 128-bit encryption)
        self.key = None

    def setKey(self, key):
        self.key = key

    # Function to encrypt a message using AES
    def encrypt_message(self, message):
        if not isinstance(message, str):
            raise ValueError("Message must be a string.")
        if not message:  # Handle empty messages
            message = " "  # Encrypt a single space instead of an empty string

        # Generate a random initialization vector (IV)
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the message to make it a multiple of the block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_message = padder.update(message.encode()) + padder.finalize()

        # Encrypt the message
        encrypted_message = encryptor.update(padded_message) + encryptor.finalize()

        # Return IV concatenated with the encrypted message
        return iv + encrypted_message

    # Function to decrypt a message
    def decrypt_message(self, encrypted_message):
        if len(encrypted_message) < 16:
            raise ValueError("Invalid encrypted message. Must include at least 16 bytes for IV.")

        # Extract the IV and the ciphertext
        iv = encrypted_message[:16]
        ciphertext = encrypted_message[16:]

        # Create cipher
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt and unpad the message
        padded_message = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        message = unpadder.update(padded_message) + unpadder.finalize()

        try:
            # Attempt to decode the message as a UTF-8 string
            return message.decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, return the raw bytes
            return message

