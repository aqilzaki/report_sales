import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models import Reseller


def authenticate_user(kode, pin):
    user = Reseller.query.filter_by(kode=kode).first()
    if not user:
        return None, "User tidak ditemukan"

    # karena PIN plain text
    if user.pin != pin:
        return None, "PIN salah"

    # generate JWT
    token = jwt.encode({
        "sub": user.kode,
        "exp": datetime.utcnow() + timedelta(hours=6)
    }, current_app.config["SECRET_KEY"], algorithm="HS256")

    return token, None


def get_user_from_token(token):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        kode = payload["sub"]
        user = Reseller.query.filter_by(kode=kode).first()
        return user
    except Exception:
        return None
