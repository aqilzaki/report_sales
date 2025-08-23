from flask_restx import Resource
from flask import request
from .dto import AuthDto
from . import controller as ctrl

api = AuthDto.api


@api.route("/login")
class LoginResource(Resource):
    @api.expect(AuthDto.login_request, validate=True)
    @api.marshal_with(AuthDto.login_response)
    def post(self):
        """Login reseller dengan kode + pin"""
        data = request.json
        kode = data.get("kode")
        pin = data.get("pin")

        token, error = ctrl.authenticate_user(kode, pin)
        if error:
            return {"status": "error", "message": error, "token": None}, 401

        return {"status": "success", "message": "Login berhasil", "token": token}, 200


@api.route("/me")
class MeResource(Resource):
    @api.marshal_with(AuthDto.user_info)
    def get(self):
        """Ambil info user dari JWT"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"message": "Token tidak ada"}, 401

        token = auth_header.split(" ")[1]
        user = ctrl.get_user_from_token(token)
        if not user:
            return {"message": "Token tidak valid"}, 401

        return {"kode": user.kode, "nama": user.nama}, 200
