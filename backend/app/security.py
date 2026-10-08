"""Auth primitives: PBKDF2 hashing, stdlib HS256 JWT, OTP helpers."""
import base64, hashlib, hmac, json, os, secrets, time

DEV_SECRET = "dev-secret-change-me"


def _secret() -> str:
    return os.environ.get("SKILLHUB_SECRET", DEV_SECRET)


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(8)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 120_000).hex()
    return f"pbkdf2${salt}${dk}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
        cand = hashlib.pbkdf2_hmac("sha256", pw.encode(),
                                   bytes.fromhex(salt), 120_000).hex()
        return hmac.compare_digest(cand, dk)
    except Exception:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _pad(x: str) -> str:
    return x + "=" * (-len(x) % 4)


def create_token(sub, role: str, hours: int = 12) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(json.dumps({"sub": str(sub), "role": role,
                               "exp": int(time.time()) + hours * 3600}).encode())
    body = header + "." + payload
    sig = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).digest()
    return body + "." + _b64(sig)


def decode_token(token: str):
    try:
        h, p, s = token.split(".")
        want = _b64(hmac.new(_secret().encode(), (h + "." + p).encode(),
                             hashlib.sha256).digest())
        if not hmac.compare_digest(want, s):
            return None
        data = json.loads(base64.urlsafe_b64decode(_pad(p)))
        return data if data.get("exp", 0) >= time.time() else None
    except Exception:
        return None


def gen_otp(digits: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(digits))


def password_ok(pw: str) -> bool:  # SRS FR6: >=8 chars, 1 upper, 1 digit
    return (len(pw) >= 8 and any(c.isupper() for c in pw)
            and any(c.isdigit() for c in pw))


def phone_ok(p: str) -> bool:  # SRS FR1: 11-digit BD number
    return p.isdigit() and len(p) == 11 and p.startswith("01")
