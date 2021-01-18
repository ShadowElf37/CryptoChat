from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import Salsa20, PKCS1_OAEP
from Crypto.Hash import SHA3_512
from Crypto.Signature import pkcs1_15
import os.path


def hash(text: str):
    return SHA3_512.new(text.encode())

def make_session_key(bits=256):
    return get_random_bytes(bits // 8)

# VERIFICATION
# pkcs1_15.new(public_key).verify(hash(msg), signature)


class Asymmetric:
    @staticmethod
    def make_certificate(username, password, f='cert.pem') -> RSA.RsaKey:
        key = RSA.generate(4096)
        with open(f, 'wb') as cert:
            cert.write(key.export_key('PEM', username+password))
        return key

    @staticmethod
    def load_certificate(username, password, f='cert.pem') -> RSA.RsaKey:
        with open(f, 'rb') as cert:
            return RSA.import_key(cert.read(), username+password)

    def __init__(self, username, password, cert='cert.pem'):
        if os.path.exists(cert):
            print('Loading %s...' % cert)
            self.key = self.load_certificate(username, password, cert)
        else:
            print('Creating new certificate in %s...' % cert)
            self.key = self.make_certificate(username, password, cert)
        print('Done! Key is %s bits.' % self.key.size_in_bits())

        self.public_key = self.key.publickey()

        self._en_cipher = PKCS1_OAEP.new(self.public_key)
        self._de_cipher = PKCS1_OAEP.new(self.key)

        self.signer = pkcs1_15.new(self.key)

    def encrypt(self, msg: bytes) -> bytes:
        return self._en_cipher.encrypt(msg)

    def decrypt(self, msg: bytes) -> bytes:
        return self._de_cipher.decrypt(msg)

    def generate_signature(self, msg: str) -> bytes:
        return self.signer.sign(hash(msg))


class Symmetric:
    def __init__(self, key=make_session_key(bits=256)):
        self.key = key
        self._en_cipher = Salsa20.new(key)

    def encrypt(self, msg: str) -> bytes:
        return self._en_cipher.encrypt(msg.encode()) + self._en_cipher.nonce

    def decrypt(self, msg: bytes) -> str:
        cipher = Salsa20.new(key=self.key, nonce=msg[-8:])
        return cipher.decrypt(msg[:-8]).decode()


if __name__ == '__main__':
    asym = Asymmetric('hello', 'world')
    msg = 'hello world!'
    e = asym.encrypt(msg.encode())
    d = asym.decrypt(e)
    print(e)
    print(d)

