import socket
from Security.Encryption import *

# ADDR = ('0.0.0.0', 8085)
ADDR = ('127.0.0.1', 8085)
# ADDR = ('10.20.180.13', 8085)
# ADDR = ('10.168.63.240', 8085)
# ADDR = ('10.168.63.28', 8085)

class ConnectionWithDatabase:
    def __init__(self, user_id):
        self.user_id = user_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connected = False
        self.enc = Encryption()
        self.client = None
        self.connect()

    # region   ====================     KEY EXCHANGE   =======================
    def key_exchange(self):
        pass
    #endregion

    def connect(self):
        if self.connected:
            print(f"User {self.user_id} is already connected. Skipping reconnect.")
            return  # ✅ Prevent reconnecting
        # try:
        self.socket.connect(ADDR)
        self.connected = True

        # Receive the RSA public key from the server
        binPubKey = self.socket.recv(1024)
        pubKeyObj = RSA.import_key(binPubKey)
        cipher_rsa = PKCS1_OAEP.new(pubKeyObj)
        enc_aes_key = cipher_rsa.encrypt(self.enc.key)
        # Send AES key encrypted by public key
        self.socket.send(enc_aes_key)

        # self.key_exchange()

        print(f"User {self.user_id} connected to the database.")
        self.send("HELLO_")
        # except socket.error as e:
        #     print(f"Connection failed for {self.user_id}: {e}")

    def send(self, message):
        try:
            encrypted_message = self.enc.encrypt_message(message)
            message_length = len(encrypted_message).to_bytes(4, byteorder='big')
            self.socket.send(message_length + encrypted_message)
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive(self):
        try:
            message = self.socket.recv(8192)
            if not message:
                print(f"User {self.user_id} disconnected.")
                self.close()  # ✅ Ensure proper disconnection
                return "ENDED"
            return self.enc.decrypt_message(message[4:])  # Skip length prefix
        except Exception as e:
            print(f"Receive error for {self.user_id}: {e}")
            self.close()  # ✅ Close socket on error
            return "ENDED"

    def close(self):
        """Close the connection properly."""
        if self.connected:
            print(f"Closing connection for {self.user_id}.")
            self.send(f"END")
            self.connected = False
            try:
                self.socket.shutdown(socket.SHUT_RDWR)  # ✅ Properly shutdown the socket
            except Exception as e:
                print(f"Error shutting down socket: {e}")
            self.socket.close()
