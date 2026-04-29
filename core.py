import jwt

SECRET_KEY = "my-secret-key"

# Encode a token using HS256
token = jwt.encode({"user": "admin", "role": "superuser"}, SECRET_KEY, algorithm="HS256")

# Vulnerable: passing a list of algorithms allows an attacker to forge
# signatures by exploiting algorithm confusion (e.g. switching from RS256
# to HS256 using a public key as the HMAC secret).
decoded = jwt.decode(token, SECRET_KEY, True, ["HS256", "RS256"])
print("Decoded payload:", decoded)
