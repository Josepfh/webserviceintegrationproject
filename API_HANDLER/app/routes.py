from flask import Blueprint, request, jsonify
from app import utils

main = Blueprint('main',__name__)


@main.route("/authenticate", methods=['POST'])
def authenticate():
    if not request.headers.get('x-forwarded-for'):
        return utils.error_template('Bad request'), 400
    data = request.form
    if not data.get('username') or not data.get('password'):
        #Empty username or password case
        return utils.error_template("Unauthorized due to invalid username or password."),401
    return utils.authenticate_user_password(username=data['username'], password=data['password'])

@main.route("/authenticate/<token>", methods=['GET'])
def validate(token):
    if not request.headers.get('x-forwarded-for'):
        return utils.error_template('Bad request'), 400
    return utils.validate_token(token)


@main.route("/loads",methods=['GET'])
def loads():
    auth = request.headers.get('Authorization')
    if not auth:
        return utils.error_template('Bad request'), 400
    try:
        auth = auth.split('=')[1]
    except:
        return utils.error_template('Bad request'), 400
    return utils.get_loads(auth)
