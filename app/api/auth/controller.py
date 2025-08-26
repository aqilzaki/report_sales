import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models import Reseller


def authenticate_user(kode, pin):
    user = Reseller.query.filter_by(kode=kode).first()
    if not user:
        return None, "User tidak ditemukan"

    # PIN plain text
    if user.pin != pin:
        return None, "PIN salah"

    # Generate JWT
    payload = {
        "sub": user.kode,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=6)
    }

    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    # Jika PyJWT return bytes → decode ke str
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token, None


def get_user_from_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
        kode = payload.get("sub")
        if not kode:
            return None
        return Reseller.query.filter_by(kode=kode).first()
    except jwt.ExpiredSignatureError:
        # Token expired
        return None
    except jwt.InvalidTokenError:
        # Token invalid
        return None
