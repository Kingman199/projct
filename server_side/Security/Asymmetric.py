from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto import Random

class Asymmetric:

    def __init__(self):
        # Generate RSA key pair for public-key encryption
        random_generator = Random.new().read
        key = RSA.generate(2048, random_generator)
        binPrivKey = key.exportKey()
        self.binPubKey = key.publickey().exportKey()
        privKeyObj = RSA.importKey(binPrivKey)
        pubKeyObj = RSA.importKey(self.binPubKey)
        self.cipher_rsa = PKCS1_OAEP.new(privKeyObj)  # Private key for decrypting on the server side

