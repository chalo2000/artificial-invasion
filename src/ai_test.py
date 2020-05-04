import unittest
import json
import requests
from app import app
from threading import Thread
from time import sleep
from copy import copy

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:5000"

# Sample request bodies
SAMPLE_USER = {"username": "chalo2000"}
SAMPLE_CHARACTER = {"name": "Chalos"}
SAMPLE_WEAPON = {"name": "Rubber Duck", "atk": 1337}
SAMPLE_BATTLE = lambda chal_id, o_id=None: {"challenger_id": chal_id, "opponent_id": o_id}
SAMPLE_LOG = {"timestamp": 1234, "challenger_hp": 20, "opponent_hp": 20, "action": "COVID Outbreak"}
SAMPLE_REQUEST = lambda kind, s_id, r_id=None: {"kind": kind, "sender_id": s_id, "receiver_id": r_id}

# API Documentation error messages
USER_BAD_REQUEST = "Provide a proper request of the form {username: string}"
USER_NOT_FOUND = "This user does not exist!"

CHARACTER_BAD_REQUEST = "Provide a proper request of the form {name: string}"
CHARACTER_FORBIDDEN = "This character does not belong to the provided user!"
CHARACTER_USER_NOT_FOUND = "The provided user does not exist!"
CHARACTER_NOT_FOUND = "This character does not exist!"

WEAPON_BAD_REQUEST = 'Provide a proper request of the form {name: string, atk: number}'
WEAPON_NOT_FOUND = "This weapon does not exist!"

BATTLE_BAD_REQUEST = 'Provide a proper request of the form {challenger_id: number, opponent_id?: number}'
BATTLE_CHALLENGER_FORBIDDEN = "The challenger is already in a battle!"
BATTLE_OPPONENT_FORBIDDEN = "The opponent is already in a battle!"
BATTLE_SAME_FORBIDDEN = "The challenger and opponent belong to the same user!"
BATTLE_CHALLENGER_NOT_FOUND = "The challenger character does not exist!"
BATTLE_OPPONENT_NOT_FOUND = "The opponent character does not exist!"
BATTLE_NOT_FOUND = "This battle does not exist!"

LOG_BAD_REQUEST = 'Provide a proper request of the form {timestamp: number, challenger_hp: number, \
opponent_hp: number, action: string}'
LOG_FORBIDDEN = "This log does not belong to the provided battle!"
LOG_BATTLE_NOT_FOUND = "The provided battle does not exist!"
LOG_NOT_FOUND = "This log does not exist!"

REQUEST_BAD_REQUEST = "Provide a proper request of the form {kind: string, sender_id: number, \
receiver_id: number}"
REQUEST_BAD_REQUEST_KIND = "Field kind must be either friend or battle"
REQUEST_FRIEND_YOURSELF_FORBIDDEN = "You can’t send a friend request to yourself!"
REQUEST_FRIEND_PENDING_FORBIDDEN = "There is already a pending friend request between these users!"
REQUEST_FRIEND_ALREADY_FORBIDDEN = "You are already friends!"
REQUEST_BATTLE_PENDING_FORBIDDEN = "There is already a pending battle request between these characters!"
REQUEST_BATTLE_SENDER_FORBIDDEN = "The sender is already in a battle!"
REQUEST_BATTLE_RECEIVER_FORBIDDEN = "The receiver is already in a battle!"
REQUEST_BATTLE_SAME_FORBIDDEN = "The provided characters belong to the same user!"
REQUEST_FRIEND_SENDER_NOT_FOUND = "The sending user does not exist!"
REQUEST_FRIEND_RECEIVER_NOT_FOUND = "The receiving user does not exist!"
REQUEST_BATTLE_SENDER_NOT_FOUND = "The sending character does not exist!"
REQUEST_BATTLE_RECEIVER_NOT_FOUND = "The receiving character does not exist!"
REQUEST_NOT_FOUND = "This request does not exist!"

# Request endpoint generators
def gen_users_path(user_id=None):
    base_path = f"{LOCAL_URL}/api/users"
    return base_path + "/" if user_id is None else f"{base_path}/{str(user_id)}/"

def gen_characters_path(user_id, character_id=None):
    base_path = f"{LOCAL_URL}/api/users/{str(user_id)}/characters"
    return base_path + "/" if character_id is None else f"{base_path}/{str(character_id)}/"

def gen_weapons_path(weapon_id=None):
    base_path = f"{LOCAL_URL}/api/weapons"
    return base_path + "/" if weapon_id is None else f"{base_path}/{str(weapon_id)}/"

def gen_battles_path(battle_id=None):
    base_path = f"{LOCAL_URL}/api/battles"
    return base_path + "/" if battle_id is None else f"{base_path}/{str(battle_id)}/"

def gen_logs_path(battle_id, log_id=None):
    base_path = f"{LOCAL_URL}/api/battles/{str(battle_id)}/logs"
    return base_path + "/" if log_id is None else f"{base_path}/{str(log_id)}/"

def gen_requests_path(request_id=None):
    base_path = f"{LOCAL_URL}/api/requests"
    return base_path + "/" if request_id is None else f"{base_path}/{str(request_id)}/"

# Request helpers
def get_user(user_id=None, code=200):
    if user_id:
        res = requests.get(gen_users_path(user_id))
    else:
        res = requests.get(gen_users_path())
    assert res.status_code == code
    return unwrap_response(res)

def create_user(data=SAMPLE_USER, code=201):
    res = requests.post(gen_users_path(), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def delete_user(user_id, code=202):
    res = requests.delete(gen_users_path(user_id))
    assert res.status_code == code
    return unwrap_response(res)

def create_character(user_id, data=SAMPLE_CHARACTER, code=201):
    res = requests.post(gen_characters_path(user_id), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def get_character(user_id, character_id, code=200):
    res = requests.get(gen_characters_path(user_id, character_id))
    assert res.status_code == code
    return unwrap_response(res)

def delete_character(user_id, character_id, code=202):
    res = requests.delete(gen_characters_path(user_id, character_id))
    assert res.status_code == code
    return unwrap_response(res)

def get_weapon(weapon_id=None, code=200):
    if weapon_id:
        res = requests.get(gen_weapons_path(weapon_id))
    else:
        res = requests.get(gen_weapons_path())
    assert res.status_code == code
    return unwrap_response(res)

def create_weapon(data=SAMPLE_WEAPON, code=201):
    res = requests.post(gen_weapons_path(), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def delete_weapon(weapon_id, code=202):
    res = requests.delete(gen_weapons_path(weapon_id))
    assert res.status_code == code
    return unwrap_response(res)

def create_battle(data, code=201):
    res = requests.post(gen_battles_path(), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def create_pvp_battle(code=201):
    challenger_user_id = create_user()["data"]["id"]
    challenger_id = create_character(challenger_user_id)["data"]["id"]
    opponent_user_id = create_user()["data"]["id"]
    opponent_id = create_character(opponent_user_id)["data"]["id"]
    battle = SAMPLE_BATTLE(challenger_id, opponent_id)
    return create_battle(battle, code)

def create_ai_battle(code=201):
    challenger_user_id = create_user()["data"]["id"]
    challenger_id = create_character(challenger_user_id)["data"]["id"]
    battle = SAMPLE_BATTLE(challenger_id)
    return create_battle(battle, code)

def get_battle(battle_id, code=200):
    res = requests.get(gen_battles_path(battle_id))
    assert res.status_code == code
    return unwrap_response(res)

def delete_battle(battle_id, code=202):
    res = requests.delete(gen_battles_path(battle_id))
    assert res.status_code == code
    return unwrap_response(res)

def create_log(battle_id, data=SAMPLE_LOG, code=201):
    res = requests.post(gen_logs_path(battle_id), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def get_log(battle_id, log_id, code=200):
    res = requests.get(gen_logs_path(battle_id, log_id))
    assert res.status_code == code
    return unwrap_response(res)

def delete_log(battle_id, log_id, code=202):
    res = requests.delete(gen_logs_path(battle_id, log_id))
    assert res.status_code == code
    return unwrap_response(res)

def get_request(request_id=None, code=200):
    res = requests.get(gen_requests_path(request_id))
    assert res.status_code == code
    return unwrap_response(res)

def build_request(kind):
    sender_id = create_user()["data"]["id"]
    receiver_id = create_user()["data"]["id"]
    return SAMPLE_REQUEST(kind, sender_id, receiver_id)

def create_request(data, code=201):
    res = requests.post(gen_requests_path(), data=json.dumps(data))
    assert res.status_code == code
    return unwrap_response(res)

def delete_request(request_id, code=202):
    res = requests.delete(gen_requests_path(request_id))
    assert res.status_code == code
    return unwrap_response(res)

def bad_request_checker(sample, create, error, nullable=None):
    for (field, value) in sample.items():
        # Check incorrect field type
        wrong_type = copy(sample)
        f_type = type(value)
        if f_type == str:
            wrong_type[field] = 42
        elif f_type == int:
            wrong_type[field] = "bad"
        body = create(wrong_type, 400)
        assert not body["success"]
        assert body["error"] == error
        
        if nullable and field in nullable:
            continue

        # Check missing field
        missing_field = copy(sample)
        del missing_field[field]
        body = create(missing_field, 400)
        assert not body["success"]
        assert body["error"] == error

# Response handler for unwrapping jsons, provides more useful error messages
def unwrap_response(response, body={}):
    try:
        return response.json()
    except:
        req = response.request
        raise Exception(f"""
            Error encountered on the following request:

            request path: {req.url}
            request method: {req.method}
            request body: {str(body)}

            There is an uncaught-exception being thrown in your
            method handler for this route!
            """)

class TestRoutes(unittest.TestCase):
    
    ###########
    #  USERS  #
    ###########

    def test_get_initial_users(self):
        assert get_user()["success"]
    
    def test_create_user(self):
        body = create_user()
        user = body["data"]
        assert body["success"]
        assert user["username"] == SAMPLE_USER["username"]
        assert user["characters"] == []
        assert user["friends"] == []
    
    def test_create_user_bad_request(self):
        bad_request_checker(SAMPLE_USER, create_user, USER_BAD_REQUEST)
    
    def test_get_user(self):
        user_id = create_user()["data"]["id"]
        assert get_user(user_id)["success"]

    def test_get_invalid_user(self):
        body = get_user(100000, 404)
        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND

    def test_delete_user(self):
        user_id = create_user()["data"]["id"]
        assert delete_user(user_id)["success"]
        
        body = get_user(user_id, 404)
        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND

    def test_delete_invalid_user(self):
        body = delete_user(100000, 404)
        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND
    
    ################
    #  CHARACTERS  #
    ################

    def test_create_character(self):
        user_id = create_user()["data"]["id"]

        body = create_character(user_id)
        character = body["data"]
        assert body["success"]
        assert character["name"] == SAMPLE_CHARACTER["name"]
        assert character["mhp"] == 10
        assert character["atk"] == 2
        assert character["equipped"] == None

    def test_create_character_bad_request(self):
        user_id = create_user()["data"]["id"]
        wrapper = lambda data, code: create_character(user_id, data, code)

        bad_request_checker(SAMPLE_CHARACTER, wrapper, CHARACTER_BAD_REQUEST)

    def test_create_character_invalid_user(self):
        body = create_character(100000, code=404)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND
    
    def test_get_character(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        assert get_character(user_id, character_id)["success"]

    def test_get_forbidden_character(self):
        first_user_id = create_user()["data"]["id"]
        first_character_id = create_character(first_user_id)["data"]["id"]
        second_user_id = create_user()["data"]["id"]

        body = get_character(second_user_id, first_character_id, 403)
        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

    def test_get_character_invalid_user(self):
        body = get_character(100000, 0, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND

    def test_get_invalid_character(self):
        user_id = create_user()["data"]["id"]

        body = get_character(user_id, 100000, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_delete_character(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        assert delete_character(user_id, character_id)["success"]

        body = get_character(user_id, character_id, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_delete_forbidden_character(self):
        first_user_id = create_user()["data"]["id"]
        first_character_id = create_character(first_user_id)["data"]["id"]
        second_user_id = create_user()["data"]["id"]

        body = delete_character(second_user_id, first_character_id, 403)
        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

    def test_delete_character_invalid_user(self):
        body = delete_character(100000, 0, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND

    def test_delete_invalid_character(self):
        user_id = create_user()["data"]["id"]

        body = delete_character(user_id, 100000, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    #############
    #  WEAPONS  #
    #############

    def test_get_initial_weapons(self):
        assert get_weapon()["success"]

    def test_create_weapon(self):
        body = create_weapon()
        weapon = body["data"]
        assert body["success"]
        assert weapon["name"] == SAMPLE_WEAPON["name"]
        assert weapon["atk"] == SAMPLE_WEAPON["atk"]

    def test_create_weapon_bad_request(self):
        bad_request_checker(SAMPLE_WEAPON, create_weapon, WEAPON_BAD_REQUEST)

    def test_get_weapon(self):
        weapon_id = create_weapon()["data"]["id"]
        assert get_weapon(weapon_id)["success"]

    def test_get_invalid_weapon(self):
        body = get_weapon(100000, 404)
        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    def test_delete_weapon(self):
        weapon_id = create_weapon()["data"]["id"]
        assert delete_weapon(weapon_id)["success"]

        body = get_weapon(weapon_id, 404)
        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    def test_delete_invalid_weapon(self):
        body = delete_weapon(100000, 404)
        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    #############
    #  BATTLES  #
    #############

    def test_create_pvp_battle(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        opponent_user_id = create_user()["data"]["id"]
        opponent_id = create_character(opponent_user_id)["data"]["id"]
        pvp_battle = SAMPLE_BATTLE(challenger_id, opponent_id)

        body = create_battle(pvp_battle)
        battle = body["data"]
        assert body["success"]
        assert battle["challenger_id"] == pvp_battle["challenger_id"]
        assert battle["opponent_id"] == pvp_battle["opponent_id"]
        # TODO: assert for log
        assert battle["done"] == False

    def test_create_ai_battle(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        ai_battle = SAMPLE_BATTLE(challenger_id)

        body = create_battle(ai_battle)
        battle = body["data"]
        assert body["success"]
        assert battle["challenger_id"] == ai_battle["challenger_id"]
        assert battle["opponent_id"] == None
        # TODO: assert for log
        assert battle["done"] == False

    def test_create_battle_bad_request(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        opponent_user_id = create_user()["data"]["id"]
        opponent_id = create_character(opponent_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(challenger_id, opponent_id)

        bad_request_checker(battle, create_battle, BATTLE_BAD_REQUEST, nullable=["opponent_id"])

    def test_create_forbidden_battle_challenger(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(challenger_id)
        create_battle(battle)

        new_foe_user_id = create_user()["data"]["id"]
        new_foe_id = create_character(new_foe_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(challenger_id, new_foe_id)
        
        body = create_battle(battle, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_CHALLENGER_FORBIDDEN

    def test_create_forbidden_battle_opponent(self):
        opponent_user_id = create_user()["data"]["id"]
        opponent_id = create_character(opponent_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(opponent_id)
        create_battle(battle)

        new_foe_user_id = create_user()["data"]["id"]
        new_foe_id = create_character(new_foe_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(new_foe_id, opponent_id)
        
        body = create_battle(battle, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_OPPONENT_FORBIDDEN

    def test_create_forbidden_battle_same(self):
        same_user_id = create_user()["data"]["id"]
        challenger_id = create_character(same_user_id)["data"]["id"]
        opponent_id = create_character(same_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(challenger_id, opponent_id)
        
        body = create_battle(battle, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_SAME_FORBIDDEN

    def test_create_battle_invalid_challenger(self):
        opponent_user_id = create_user()["data"]["id"]
        opponent_id = create_character(opponent_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(100000, opponent_id)

        body = create_battle(battle, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_CHALLENGER_NOT_FOUND

    def test_create_battle_invalid_opponent(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(challenger_id, 100000)

        body = create_battle(battle, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_OPPONENT_NOT_FOUND

    def test_get_battle(self):
        battle_id = create_pvp_battle()["data"]["id"]
        assert get_battle(battle_id)["success"]

    def test_get_invalid_battle(self):
        body = get_battle(100000, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_NOT_FOUND

    def test_delete_battle(self):
        battle_id = create_pvp_battle()["data"]["id"]
        assert delete_battle(battle_id)["success"]
        
        body = get_battle(battle_id, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_NOT_FOUND

    def test_delete_invalid_battle(self):
        body = delete_battle(100000, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_NOT_FOUND

    ##########
    #  LOGS  #
    ##########

    def test_create_log(self):
        battle_id = create_ai_battle()["data"]["id"] # we create one less user/character using ai instead of pvp
        body = create_log(battle_id)
        log = body["data"]
        assert body["success"]
        assert log["timestamp"] == SAMPLE_LOG["timestamp"]
        assert log["challenger_hp"] == SAMPLE_LOG["challenger_hp"]
        assert log["opponent_hp"] == SAMPLE_LOG["opponent_hp"]
        assert log["action"] == SAMPLE_LOG["action"]

    def test_create_log_bad_request(self):
        battle_id = create_ai_battle()["data"]["id"]
        wrapper = lambda data, code: create_log(battle_id, data, code)

        bad_request_checker(SAMPLE_LOG, wrapper, LOG_BAD_REQUEST)

    def test_create_log_invalid_battle(self):
        body = create_log(100000, code=404)
        assert not body["success"]
        assert body["error"] == LOG_BATTLE_NOT_FOUND
        
    def test_get_log(self):
        battle_id = create_ai_battle()["data"]["id"]
        log_id = create_log(battle_id)["data"]["id"]
        assert get_log(battle_id, log_id)

    def test_get_forbidden_log(self):
        first_battle_id = create_ai_battle()["data"]["id"]
        first_log_id = create_log(first_battle_id)["data"]["id"]
        second_battle_id = create_ai_battle()["data"]["id"]

        body = get_log(second_battle_id, first_log_id, 403)
        assert not body["success"]
        assert body["error"] == LOG_FORBIDDEN

    def test_get_log_invalid_battle(self):
        body = get_log(100000, 0, 404)
        assert not body["success"]
        assert body["error"] == LOG_BATTLE_NOT_FOUND

    def test_get_invalid_log(self):
        battle_id = create_ai_battle()["data"]["id"]

        body = get_log(battle_id, 100000, 404)
        assert not body["success"]
        assert body["error"] == LOG_NOT_FOUND

    def test_delete_log(self):
        battle_id = create_ai_battle()["data"]["id"]
        log_id = create_log(battle_id)["data"]["id"]
        assert delete_log(battle_id, log_id)["success"]

        body = get_log(battle_id, log_id, 404)
        assert not body["success"]
        assert body["error"] == LOG_NOT_FOUND

    def test_delete_forbidden_log(self):
        first_battle_id = create_ai_battle()["data"]["id"]
        first_log_id = create_log(first_battle_id)["data"]["id"]
        second_battle_id = create_ai_battle()["data"]["id"]

        body = delete_log(second_battle_id, first_log_id, 403)
        assert not body["success"]
        assert body["error"] == LOG_FORBIDDEN

    def test_delete_log_invalid_user(self):
        body = delete_log(100000, 0, 404)
        assert not body["success"]
        assert body["error"] == LOG_BATTLE_NOT_FOUND

    def test_delete_invalid_log(self):
        battle_id = create_ai_battle()["data"]["id"]

        body = delete_log(battle_id, 100000, 404)
        assert not body["success"]
        assert body["error"] == LOG_NOT_FOUND

    ##############
    #  REQUESTS  #
    ##############

    def test_create_request(self):
        sample_request = build_request("friend") # input does not matter
        body = create_request(sample_request)
        request = body["data"]
        assert body["success"]
        assert request["kind"] == sample_request["kind"]
        assert request["sender_id"] == sample_request["sender_id"]
        assert request["receiver_id"] == sample_request["receiver_id"]
        assert request["accepted"] == None

    def test_create_request_bad_request(self):
        req = build_request("battle") # input does not matter
        return bad_request_checker(req, create_request, REQUEST_BAD_REQUEST)

    def test_create_request_bad_request_kind(self):
        body = create_request(build_request("d'oh"), 400)
        assert not body["success"]
        assert body["error"] == REQUEST_BAD_REQUEST_KIND

    def test_create_friend_request_forbidden_yourself(self):
        same_user_id = create_user()["data"]["id"]
        body = create_request(SAMPLE_REQUEST("friend", same_user_id, same_user_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_YOURSELF_FORBIDDEN

    def test_create_friend_request_forbidden_pending(self):
        sender_id = create_user()["data"]["id"]
        receiver_id = create_user()["data"]["id"]
        create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id))

        body = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_PENDING_FORBIDDEN

        body = create_request(SAMPLE_REQUEST("friend", receiver_id, sender_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_PENDING_FORBIDDEN
    
    
    def test_create_friend_request_forbidden_already(self):
        pass # Add friend creation functionality first

    def test_create_battle_request_forbidden_pending(self):
        sending_user_id = create_user()["data"]["id"]
        sender_id = create_character(sending_user_id)["data"]["id"]
        receiving_user_id = create_user()["data"]["id"]
        receiver_id = create_character(receiving_user_id)["data"]["id"]
        create_request(SAMPLE_REQUEST("battle", sender_id, receiver_id))

        body = create_request(SAMPLE_REQUEST("battle", sender_id, receiver_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_PENDING_FORBIDDEN

        body = create_request(SAMPLE_REQUEST("battle", receiver_id, sender_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_PENDING_FORBIDDEN

    def test_create_battle_request_forbidden_sender(self):
        sending_user_id = create_user()["data"]["id"]
        sender_id = create_character(sending_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(sender_id)
        create_battle(battle)

        receiving_user_id = create_user()["data"]["id"]
        receiver_id = create_character(receiving_user_id)["data"]["id"]
        request = SAMPLE_REQUEST("battle", sender_id, receiver_id)

        body = create_request(request, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_SENDER_FORBIDDEN
    
    def test_create_battle_request_forbidden_receiver(self):
        sending_user_id = create_user()["data"]["id"]
        sender_id = create_character(sending_user_id)["data"]["id"]

        receiving_user_id = create_user()["data"]["id"]
        receiver_id = create_character(receiving_user_id)["data"]["id"]
        battle = SAMPLE_BATTLE(receiver_id)
        create_battle(battle)

        request = SAMPLE_REQUEST("battle", sender_id, receiver_id)

        body = create_request(request, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_RECEIVER_FORBIDDEN

    def test_create_battle_request_forbidden_same(self):
        same_user_id = create_user()["data"]["id"]
        sender_id = create_character(same_user_id)["data"]["id"]
        receiver_id = create_character(same_user_id)["data"]["id"]
        request = SAMPLE_REQUEST("battle", sender_id, receiver_id)

        body = create_request(request, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_SAME_FORBIDDEN

    def test_create_friend_request_sender_not_found(self):
        receiver_id = create_user()["data"]["id"]
        request = SAMPLE_REQUEST("friend", 100000, receiver_id)
        
        body = create_request(request, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_SENDER_NOT_FOUND

    def test_create_friend_request_receiver_not_found(self):
        sender_id = create_user()["data"]["id"]
        request = SAMPLE_REQUEST("friend", sender_id, 100000)
        
        body = create_request(request, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_RECEIVER_NOT_FOUND

    def test_create_battle_request_sender_not_found(self):
        receiving_user_id = create_user()["data"]["id"]
        receiver_id = create_character(receiving_user_id)["data"]["id"]
        request = SAMPLE_REQUEST("battle", 100000, receiver_id)
        
        body = create_request(request, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_SENDER_NOT_FOUND

    def test_create_battle_request_receiver_not_found(self):
        sending_user_id = create_user()["data"]["id"]
        sender_id = create_character(sending_user_id)["data"]["id"]
        request = SAMPLE_REQUEST("battle", sender_id, 100000)
        
        body = create_request(request, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_RECEIVER_NOT_FOUND

    def test_get_request(self):
        request_id = create_request(build_request("friend"))["data"]["id"] # input doesn't matter
        body = get_request(request_id)
        assert body["success"]

    def test_get_invalid_request(self):
        body = get_request(100000, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_NOT_FOUND

    def test_delete_request(self):
        request_id = create_request(build_request("friend"))["data"]["id"] # input doesn't matter
        body = delete_request(request_id)
        assert body["success"]

        body = get_request(request_id, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_NOT_FOUND

    def test_delete_invalid_request(self):
        body = delete_request(100000, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_NOT_FOUND

def run_tests():
    sleep(1.5)
    unittest.main()

if __name__ == "__main__":
    thread = Thread(target=run_tests)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
