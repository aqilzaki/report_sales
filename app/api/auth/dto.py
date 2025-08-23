from flask_restx import Namespace, fields

class AuthDto:
    api = Namespace("auth", description="Authentication")

    login_request = api.model("LoginRequest", {
        "kode": fields.String(required=True, description="Kode reseller"),
        "pin": fields.String(required=True, description="PIN"),
    })

    login_response = api.model("LoginResponse", {
        "status": fields.String,
        "message": fields.String,
        "token": fields.String,
    })

    user_info = api.model("UserInfo", {
        "kode": fields.String,
        "nama": fields.String,
    })
