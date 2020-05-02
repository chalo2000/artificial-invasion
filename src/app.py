import json
from flask import Flask, request
import dao
from db import db

app = Flask(__name__)
db_filename = "ai.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

#############
#  HELPERS  #
#############

def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code

def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code

exhaustive_check = lambda body, fields: any([body.get(x[0], None) == 
                                             None for x in fields])
type_check = lambda body, fields: any([type(body.get(x[0], None)) != 
                                       x[1] for x in fields])

def is_valid(body, fields):
    return not (exhaustive_check(body, fields) or type_check(body, fields))

###########
#  PATHS  #
###########

API_PATH = "/api/"
USER_PATH = API_PATH + "users/"
SPECIFIC_USER_PATH = USER_PATH + "<int:uid>/"
CHARACTER_PATH = SPECIFIC_USER_PATH + "characters/"
SPECIFIC_CHARACTER_PATH = CHARACTER_PATH + "<int:cid>/"
WEAPON_PATH = API_PATH + "weapons/"
SPECIFIC_WEAPON_PATH = WEAPON_PATH + "<int:wid>/"
BATTLE_PATH = API_PATH + "battles/"
SPECIFIC_BATTLE_PATH = BATTLE_PATH + "<int:bid>/"
LOG_PATH = SPECIFIC_BATTLE_PATH + "logs/"
SPECIFIC_LOG_PATH = LOG_PATH + "<int:lid>/"

############
#  ROUTES  #
############

@app.route(USER_PATH)
def get_all_users():
    return success_response(dao.get_all_users())

@app.route(USER_PATH, methods=["POST"])
def create_user():
    body = json.loads(request.data)
    if not is_valid(body, [("username", str)]):
        return failure_response("Provide a proper request of the form {username: string}", 400)
    user = dao.create_user(
        username=body.get("username")
    )
    return success_response(user, 201)

@app.route(SPECIFIC_USER_PATH)
def get_user(uid):
    user = dao.get_user(uid)
    if user is None:
        return failure_response("This user does not exist!")
    return success_response(user)

@app.route(SPECIFIC_USER_PATH, methods=["DELETE"])
def delete_user(uid):
    user = dao.delete_user(uid)
    if user is None:
        return failure_response("This user does not exist!")
    return success_response(user, 202)

@app.route(CHARACTER_PATH, methods=["POST"])
def create_character(uid):
    body = json.loads(request.data)
    if not is_valid(body, [("name", str)]):
        return failure_response("Provide a proper request of the form {name: string}", 400)
    character = dao.create_character(
        name=body.get("name"),
        uid=uid
    )
    if character is None:
        return failure_response("The provided user does not exist!")
    return success_response(character, 201)

@app.route(SPECIFIC_CHARACTER_PATH)
def get_character(uid, cid):
    character, code = dao.get_character(uid, cid)
    if type(character) == str:
        return failure_response(character, code)
    return success_response(character, code)

@app.route(SPECIFIC_CHARACTER_PATH, methods=["DELETE"])
def delete_character(uid, cid):
    character, code = dao.delete_character(uid, cid)
    if type(character) == str:
        return failure_response(character, code)
    return success_response(character, code)

@app.route(WEAPON_PATH)
def get_all_weapons():
    return success_response(dao.get_all_weapons())

@app.route(WEAPON_PATH, methods=["POST"])
def create_weapon():
    body = json.loads(request.data)
    if not is_valid(body, [("name", str), ("atk", int)]):
        return failure_response("Provide a proper request of the form "
                                "{name: string, atk: number}", 400)
    weapon = dao.create_weapon(
        name=body.get("name"),
        atk=body.get("atk")
    )
    return success_response(weapon, 201)

@app.route(SPECIFIC_WEAPON_PATH)
def get_weapon(wid):
    weapon = dao.get_weapon(wid)
    if weapon is None:
        return failure_response("This weapon does not exist!")
    return success_response(weapon)

@app.route(SPECIFIC_WEAPON_PATH, methods=["DELETE"])
def delete_weapon(wid):
    weapon = dao.delete_weapon(wid)
    if weapon is None:
        return failure_response("This weapon does not exist!")
    return success_response(weapon, 202)

@app.route(BATTLE_PATH, methods=["POST"])
def create_battle():
    body = json.loads(request.data)
    if not (is_valid(body, [("challenger_id", int), ("opponent_id", int)]) or
            is_valid(body, [("challenger_id", int)]) and 
            body.get("opponent_id") is None):
        return failure_response("Provide a proper request of the form "
                        "{challenger_id: number, opponent_id?: number}", 400)
    battle, code = dao.create_battle(
        challenger_id=body.get("challenger_id"),
        opponent_id=body.get("opponent_id")
    )
    if type(battle) == str:
        return failure_response(battle, code)
    return success_response(battle, code)

@app.route(SPECIFIC_BATTLE_PATH)
def get_battle(bid):
    battle = dao.get_battle(bid)
    if battle is None:
        return failure_response("This battle does not exist!")
    return success_response(battle)

@app.route(SPECIFIC_BATTLE_PATH, methods=["DELETE"])
def delete_battle(bid):
    battle = dao.delete_battle(bid)
    if battle is None:
        return failure_response("This battle does not exist!")
    return success_response(battle, 202)

@app.route(LOG_PATH, methods=["POST"])
def create_log(bid):
    body = json.loads(request.data)
    if not is_valid(body, [("timestamp", int), ("challenger_hp", int),
                           ("opponent_hp", int), ("action", str)]):
        return failure_response("Provide a proper request of the form {timestamp: string, challenger_hp: number, opponent_hp: number, action: string}", 400)
    log = dao.create_log(
        timestamp=body.get("timestamp"),
        challenger_hp=body.get("challenger_hp"),
        opponent_hp=body.get("opponent_hp"),
        action=body.get("action"),
        bid=bid
    )
    if log is None:
        return failure_response("The provided battle does not exist!")
    return success_response(log, 201)

@app.route(SPECIFIC_LOG_PATH)
def get_log(bid, lid):
    log, code = dao.get_log(bid, lid)
    if type(log) == str:
        return failure_response(log, code)
    return success_response(log, code)

@app.route(SPECIFIC_LOG_PATH, methods=["DELETE"])
def delete_log(bid, lid):
    log, code = dao.delete_log(bid, lid)
    if type(log) == str:
        return failure_response(log, code)
    return success_response(log, code)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
