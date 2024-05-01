from OpenSSL import crypto, SSL
import random

# Generate a self-signed root CA certificate
rootkey = crypto.PKey()
rootkey.generate_key(crypto.TYPE_RSA, 2048)
rootca = crypto.X509()
rootca.get_subject().CN = "Proxy-Server"  # Replace "My Root CA" with your desired name
rootca.gmtime_adj_notBefore(10)
rootca.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
rootca.set_issuer(rootca.get_subject())
rootca.set_pubkey(rootkey)
rootca.sign(rootkey, "sha256")

# Save the root CA certificate and private key
with open("rootCA.pem", "wb") as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, rootca))
with open("rootCA.key", "wb") as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, rootkey))
