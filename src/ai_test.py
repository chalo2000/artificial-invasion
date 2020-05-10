import unittest
import json
import requests
from app import app
from threading import Thread
from time import sleep
from copy import copy
from functools import reduce

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:5000"

# Constants
MHP = 10
ATK = 2
MHP_INCREMENT = 4
ATK_INCREMENT = 2

# Sample request bodies
SAMPLE_USER_ONE = {"username": "chalo2000"}
SAMPLE_USER_TWO = {"username": "2000chalo"}
SAMPLE_END_FRIENDSHIP = lambda ex_id: {"ex_friend_id": ex_id}
SAMPLE_CHARACTER_ONE = {"name": "Chalos"}
SAMPLE_CHARACTER_TWO = {"name": "Solach"}
SAMPLE_CHARACTER_PREPARE = lambda wid: {"weapon_id": wid}
SAMPLE_WEAPON = {"name": "Rubber Duck", "atk": 1337}
SAMPLE_BATTLE = lambda chal_id, o_id=None: {"challenger_id": chal_id, "opponent_id": o_id}
SAMPLE_BATTLE_ACTION = lambda actor_id, action: {"actor_id": actor_id, "action": action}
SAMPLE_LOG = {"timestamp": 1234, "challenger_hp": 20, "opponent_hp": 20, "action": "COVID Outbreak"}
SAMPLE_REQUEST = lambda kind, s_id, r_id: {"kind": kind, "sender_id": s_id, "receiver_id": r_id}
SAMPLE_RESPONSE = lambda r_id, accepted: {"receiver_id": r_id, "accepted": accepted}

# API Documentation error messages
USER_BAD_REQUEST = "Provide a proper request of the form {username: string}"
USER_NOT_FOUND = "This user does not exist!"

USER_END_FRIENDSHIP_BAD_REQUEST = "Provide a proper request of the form {ex_friend_id: number}"
USER_END_FRIENDSHIP_FORBIDDEN_SELF = "You can never unfriend yourself!"
USER_END_FRIENDSHIP_FORBIDDEN_INVALID = "You aren’t friends with this user!"
USER_END_FRIENDSHIP_UNFRIENDER_NOT_FOUND = "The provided un-friender does not exist!"
USER_END_FRIENDSHIP_EXFRIEND_NOT_FOUND = "The provided ex-friend does not exist!"

CHARACTER_BAD_REQUEST = "Provide a proper request of the form {name: string}"
CHARACTER_FORBIDDEN = "This character does not belong to the provided user!"
CHARACTER_USER_NOT_FOUND = "The provided user does not exist!"
CHARACTER_NOT_FOUND = "This character does not exist!"

CHARACTER_PREPARE_BAD_REQUEST = "Provide a proper request of the form {weapon_id: number}"
CHARACTER_PREPARE_UNEQUIP_FORBIDDEN = "You don’t have this weapon equipped!"

WEAPON_BAD_REQUEST = 'Provide a proper request of the form {name: string, atk: number}'
WEAPON_NOT_FOUND = "This weapon does not exist!"

BATTLE_BAD_REQUEST = 'Provide a proper request of the form {challenger_id: number, opponent_id?: number}'
BATTLE_CHALLENGER_FORBIDDEN = "The challenger is already in a battle!"
BATTLE_OPPONENT_FORBIDDEN = "The opponent is already in a battle!"
BATTLE_SAME_FORBIDDEN = "The challenger and opponent belong to the same user!"
BATTLE_CHALLENGER_NOT_FOUND = "The challenger character does not exist!"
BATTLE_OPPONENT_NOT_FOUND = "The opponent character does not exist!"
BATTLE_NOT_FOUND = "This battle does not exist!"

BATTLE_ACTION_ACCEPTED = "Your action has been recorded"
BATTLE_ACTION_BAD_REQUEST = "Provide a proper request of the form {actor_id: number, action: string}"
BATTLE_ACTION_BAD_REQUEST_ACTION = "Field action must be Attack, Defend, or Counter"
BATTLE_ACTION_CHARACTER_FORBIDDEN = "This character does not belong to the provided battle!"
BATTLE_ACTION_DONE_FORBIDDEN = "The provided battle is already done!"
BATTLE_ACTION_ALREADY_FORBIDDEN = "This character has already sent an action!"
BATTLE_ACTION_BATTLE_NOT_FOUND = "The provided battle does not exist!"

LOG_STARTING_ACTION = lambda chal_name, o_name: (
    f"The battle between Challenger {chal_name} and Opponent {o_name} has begun."
)
LOG_DAMAGE_ACTION = lambda chal_name, chal_act, chal_atk, o_name, o_act, o_atk: (
    f"Challenger {chal_name} used {chal_act} and dealt {chal_atk} damage! "
    f"Opponent {o_name} used {o_act} and dealt {o_atk} damage!"
)
LOG_WINNER_ACTION = lambda winner_name: (
    f"{winner_name} has won the battle!!!"
)
LOG_DRAW_ACTION = "The battle has ended by draw"

LOG_BAD_REQUEST = 'Provide a proper request of the form {timestamp: number, challenger_hp: number, \
opponent_hp: number, action: string}'
LOG_FORBIDDEN = "This log does not belong to the provided battle!"
LOG_BATTLE_NOT_FOUND = BATTLE_ACTION_BATTLE_NOT_FOUND
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

REQUEST_RESPOND_DENIED = lambda s_name, kind: f"You have rejected {s_name}’s {kind} request"
REQUEST_RESPOND_BAD_REQUEST = "Provide a proper request of the form {receiver_id: number, accepted: boolean}"
REQUEST_RESPOND_FORBIDDEN_OWN = "You can’t respond to your own request!"
REQUEST_RESPOND_FORBIDDEN_ANOTHERS = "This request was not sent to you!"
REQUEST_RESPOND_FORBIDDEN_ACCEPTED = "This request has already been accepted!"
REQUEST_RESPOND_FORBIDDEN_DENIED = "This request has already been denied!"

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
    return unwrap_response(res, code)

def create_user(data=None, sample_type=1, code=201):
    sample_data = SAMPLE_USER_ONE if sample_type == 1 else SAMPLE_USER_TWO
    res = requests.post(gen_users_path(), 
                        data=json.dumps(sample_data if data is None else data))
    return unwrap_response(res, code, data)

def delete_user(user_id, code=202):
    res = requests.delete(gen_users_path(user_id))
    return unwrap_response(res, code)

def end_friendship(user_id, data, code=200):
    res = requests.post(gen_users_path(user_id), data=json.dumps(data))
    return unwrap_response(res, code)

def create_character(user_id, data=None, sample_type=1, code=201):
    sample_data = SAMPLE_CHARACTER_ONE if sample_type == 1 else SAMPLE_CHARACTER_TWO
    res = requests.post(gen_characters_path(user_id), 
                        data=json.dumps(sample_data if data is None else data))
    return unwrap_response(res, code, data)

def get_character(user_id, character_id, code=200):
    res = requests.get(gen_characters_path(user_id, character_id))
    return unwrap_response(res, code)

def delete_character(user_id, character_id, code=202):
    res = requests.delete(gen_characters_path(user_id, character_id))
    return unwrap_response(res, code)

def prepare_weapon(user_id, character_id, data, code=200):
    res = requests.post(gen_characters_path(user_id, character_id), data=json.dumps(data))
    return unwrap_response(res, code, data)

def get_weapon(weapon_id=None, code=200):
    if weapon_id:
        res = requests.get(gen_weapons_path(weapon_id))
    else:
        res = requests.get(gen_weapons_path())
    return unwrap_response(res, code)

def create_weapon(data=SAMPLE_WEAPON, code=201):
    res = requests.post(gen_weapons_path(), data=json.dumps(data))
    return unwrap_response(res, code, data)

def delete_weapon(weapon_id, code=202):
    res = requests.delete(gen_weapons_path(weapon_id))
    return unwrap_response(res, code)

def create_battle(data, code=201):
    res = requests.post(gen_battles_path(), data=json.dumps(data))
    return unwrap_response(res, code, data)

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
    return unwrap_response(res, code)

def delete_battle(battle_id, code=202):
    res = requests.delete(gen_battles_path(battle_id))
    return unwrap_response(res, code)

def send_battle_action(battle_id, data, code=202):
    res = requests.post(gen_battles_path(battle_id), data=json.dumps(data))
    return unwrap_response(res, code, data)

def execute_action(challenger_action, opponent_action):
    (chal_uid, chal_cid), (o_uid, o_cid), _, bid = respond_to_battle_request()
    chal_act = SAMPLE_BATTLE_ACTION(chal_cid, challenger_action)
    o_act = SAMPLE_BATTLE_ACTION(o_cid, opponent_action)
    send_battle_action(bid, chal_act)
    send_battle_action(bid, o_act)
    done_battle = get_battle(bid)["data"]
    recent_log = most_recent_log(done_battle["logs"])

    challenger = get_character(chal_uid, chal_cid)["data"]
    opponent = get_character(o_uid, o_cid)["data"]
    return (challenger["name"], challenger_action, challenger["atk"],
            opponent["name"], opponent_action, opponent["atk"],
            recent_log)

def execute_action_to_completion(chal_act, o_act):
    (chal_uid, chal_id), (o_uid, o_id), _, bid = respond_to_battle_request()
    chal_act = SAMPLE_BATTLE_ACTION(chal_id, chal_act)
    o_act = SAMPLE_BATTLE_ACTION(o_id, o_act)

    while True:
        try:
            send_battle_action(bid, chal_act)
            send_battle_action(bid, o_act)
        except:
            break
    return (chal_uid, chal_id), (o_uid, o_id), bid

def create_log(battle_id, data=SAMPLE_LOG, code=201):
    res = requests.post(gen_logs_path(battle_id), data=json.dumps(data))
    return unwrap_response(res, code, data)

def get_log(battle_id, log_id, code=200):
    res = requests.get(gen_logs_path(battle_id, log_id))
    return unwrap_response(res, code)

def delete_log(battle_id, log_id, code=202):
    res = requests.delete(gen_logs_path(battle_id, log_id))
    return unwrap_response(res, code)

def get_request(request_id=None, code=200):
    res = requests.get(gen_requests_path(request_id))
    return unwrap_response(res, code)

def build_request(kind):
    sender = create_user()["data"]
    receiver = create_user(sample_type=2)["data"]
    if kind == "battle":
        sender = create_character(sender["id"])["data"]
        receiver = create_character(receiver["id"], sample_type=2)["data"]
    return SAMPLE_REQUEST(kind, sender["id"], receiver["id"])

def create_request(data, code=201):
    res = requests.post(gen_requests_path(), data=json.dumps(data))
    return unwrap_response(res, code, data)

def delete_request(request_id, code=202):
    res = requests.delete(gen_requests_path(request_id))
    return unwrap_response(res, code)

def respond_to_request(request_id, data, code=200):
    res = requests.post(gen_requests_path(request_id), data=json.dumps(data))
    return unwrap_response(res, code, data)

def respond_to_friend_request():
    sender = create_user()["data"]
    receiver = create_user(sample_type=2)["data"]
    request = create_request(SAMPLE_REQUEST("friend", sender["id"], receiver["id"]))["data"]
    response = SAMPLE_RESPONSE(receiver["id"], True)
    body = respond_to_request(request["id"], response)
    return sender["id"], receiver["id"], request["id"], body

def respond_to_battle_request():
    sending_user_id = create_user()["data"]["id"]
    sending_char_id = create_character(sending_user_id)["data"]["id"]
    receiving_user_id = create_user(sample_type=2)["data"]["id"]
    receiving_char_id = create_character(receiving_user_id, sample_type=2)["data"]["id"]
    sample_request = SAMPLE_REQUEST("battle", sending_char_id, receiving_char_id)
    request_id = create_request(sample_request)["data"]["id"]
    response = SAMPLE_RESPONSE(receiving_char_id, True)
    battle_id = respond_to_request(request_id, response)["data"]["id"]
    return (sending_user_id, sending_char_id), (receiving_user_id, receiving_char_id), request_id, battle_id

def bad_request_checker(sample, create, error, nullable=None):
    for (field, value) in sample.items():
        # Check incorrect field type
        wrong_type = copy(sample)
        f_type = type(value)
        if f_type == str:
            wrong_type[field] = False
        elif f_type == int:
            wrong_type[field] = "bad"
        elif f_type == bool:
            wrong_type[field] = 42
        body = create(data=wrong_type, code=400)
        assert not body["success"]
        assert body["error"] == error
        
        if nullable and field in nullable:
            continue

        # Check missing field
        missing_field = copy(sample)
        del missing_field[field]
        body = create(data=missing_field, code=400)
        assert not body["success"]
        assert body["error"] == error

most_recent_log = lambda logs: reduce(lambda x, y: x if x["id"] > y["id"] else y, logs)

# Response handler for unwrapping jsons, provides more useful error messages
def unwrap_response(response, code, body={}):
    try:
        assert response.status_code == code
        return response.json()
    except AssertionError:
        req = response.request
        raise Exception(f"""
            Error encountered on the following request:

            request path: {req.url}
            request method: {req.method}
            request body: {str(body)}

            The response code we get is {response.status_code}
            but you are expecting {code}!
            """)
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

    # Get all users

    def test_get_initial_users(self):
        assert get_user()["success"]
    
    # Create a user

    def test_create_user(self):
        body = create_user()
        user = body["data"]
        assert body["success"]
        assert user["username"] == SAMPLE_USER_ONE["username"]
        assert user["characters"] == []
        assert user["friends"] == []
    
    def test_create_user_bad_request(self):
        bad_request_checker(SAMPLE_USER_ONE, create_user, USER_BAD_REQUEST)
    
    # Get a specific user

    def test_get_user(self):
        user_id = create_user()["data"]["id"]
        assert get_user(user_id)["success"]

    def test_get_invalid_user(self):
        body = get_user(100000, 404)
        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND

    # Delete a specific user

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

    # End a friendship

    def test_end_friendship(self):
        unfriender_id, ex_friend_id, _, _ = respond_to_friend_request()
        updated_unfriender = get_user(unfriender_id)["data"]
        updated_ex_friend = get_user(ex_friend_id)["data"]

        assert updated_unfriender["friends"] != []
        assert updated_ex_friend["friends"] != []

        data = SAMPLE_END_FRIENDSHIP(ex_friend_id)
        end_friendship(unfriender_id, data)
        updated_unfriender = get_user(unfriender_id)["data"]
        updated_ex_friend = get_user(ex_friend_id)["data"]

        assert updated_unfriender["friends"] == []
        assert updated_ex_friend["friends"] == []
    
    def test_end_friendship_bad_request(self):
        unfriender_id, ex_friend_id, _, _ = respond_to_friend_request()
        wrapper = lambda data, code: end_friendship(unfriender_id, data=data, code=code)
        sample = SAMPLE_END_FRIENDSHIP(ex_friend_id)

        bad_request_checker(sample, wrapper, USER_END_FRIENDSHIP_BAD_REQUEST)

    def test_end_friendship_forbidden_self(self):
        unfriender_id, _, _, _ = respond_to_friend_request()
        data = SAMPLE_END_FRIENDSHIP(unfriender_id)
        body = end_friendship(unfriender_id, data, 403)
        assert not body["success"]
        assert body["error"] == USER_END_FRIENDSHIP_FORBIDDEN_SELF

    def test_end_friendship_forbidden_invalid(self):
        unfriender_id = create_user()["data"]["id"]
        not_friend_id = create_user()["data"]["id"]
        data = SAMPLE_END_FRIENDSHIP(not_friend_id)
        body = end_friendship(unfriender_id, data, 403)
        assert not body["success"]
        assert body["error"] == USER_END_FRIENDSHIP_FORBIDDEN_INVALID

    def test_end_friendship_unfriender_not_found(self):
        ex_friend_id = create_user()["data"]["id"]
        data = SAMPLE_END_FRIENDSHIP(ex_friend_id)
        body = end_friendship(100000, data, 404)
        assert not body["success"]
        assert body["error"] == USER_END_FRIENDSHIP_UNFRIENDER_NOT_FOUND

    def test_end_friendship_exfriend_not_found(self):
        unfriender_id = create_user()["data"]["id"]
        data = SAMPLE_END_FRIENDSHIP(100000)
        body = end_friendship(unfriender_id, data, 404)
        assert not body["success"]
        assert body["error"] == USER_END_FRIENDSHIP_EXFRIEND_NOT_FOUND
    
    ################
    #  CHARACTERS  #
    ################

    # Create a character for a user

    def test_create_character(self):
        user_id = create_user()["data"]["id"]

        body = create_character(user_id)
        character = body["data"]
        assert body["success"]
        assert character["name"] == SAMPLE_CHARACTER_ONE["name"]
        assert character["mhp"] == MHP
        assert character["atk"] == ATK
        assert character["equipped"] == None

    def test_create_character_bad_request(self):
        user_id = create_user()["data"]["id"]
        wrapper = lambda data, code: create_character(user_id, data=data, code=code)

        bad_request_checker(SAMPLE_CHARACTER_ONE, wrapper, CHARACTER_BAD_REQUEST)

    def test_create_character_invalid_user(self):
        body = create_character(100000, code=404)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND
    
    # Get a user’s character

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

    # Delete a user’s character

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

    # Prepare a weapon

    def test_prepare_weapon(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        weapon = create_weapon()["data"]

        body = prepare_weapon(user_id, character_id, SAMPLE_CHARACTER_PREPARE(weapon["id"]))
        character = body["data"]
        assert body["success"]
        assert character["equipped"] == weapon

        body = prepare_weapon(user_id, character_id, SAMPLE_CHARACTER_PREPARE(weapon["id"]))
        character = body["data"]
        assert body["success"]
        assert character["equipped"] == None

    def test_prepare_weapon_bad_request(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        weapon_id = create_weapon()["data"]["id"]
        sample = SAMPLE_CHARACTER_PREPARE(weapon_id)
        wrapper = lambda data, code: prepare_weapon(user_id, character_id, data=data, code=code)
        bad_request_checker(sample, wrapper, CHARACTER_PREPARE_BAD_REQUEST)

    def test_prepare_weapon_forbidden(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        another_user_id = create_user()["data"]["id"]
        another_character_id = create_character(another_user_id)["data"]["id"]
        weapon_id = create_weapon()["data"]["id"]
        sample_prepare = SAMPLE_CHARACTER_PREPARE(weapon_id)

        body = prepare_weapon(user_id, another_character_id, sample_prepare, 403)
        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

        body = prepare_weapon(another_user_id, character_id, sample_prepare, 403)
        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

    def test_prepare_weapon_unequip_forbidden(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        weapon_id = create_weapon()["data"]["id"]
        sample_prepare = SAMPLE_CHARACTER_PREPARE(weapon_id)
        prepare_weapon(user_id, character_id, sample_prepare)

        another_weapon_id = create_weapon()["data"]["id"]
        another_sample_prepare = SAMPLE_CHARACTER_PREPARE(another_weapon_id)

        body = prepare_weapon(user_id, character_id, another_sample_prepare, 403)
        assert not body["success"]
        assert body["error"] == CHARACTER_PREPARE_UNEQUIP_FORBIDDEN

    def test_prepare_weapon_user_not_found(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        weapon_id = create_weapon()["data"]["id"]
        sample_prepare = SAMPLE_CHARACTER_PREPARE(weapon_id)
        
        body = prepare_weapon(100000, character_id, sample_prepare, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND

    def test_prepare_weapon_character_not_found(self):
        user_id = create_user()["data"]["id"]
        weapon_id = create_weapon()["data"]["id"]
        sample_prepare = SAMPLE_CHARACTER_PREPARE(weapon_id)
        
        body = prepare_weapon(user_id, 100000, sample_prepare, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_prepare_weapon_weapon_not_found(self):
        user_id = create_user()["data"]["id"]
        character_id = create_character(user_id)["data"]["id"]
        sample_prepare = SAMPLE_CHARACTER_PREPARE(100000)
        
        body = prepare_weapon(user_id, character_id, sample_prepare, 404)
        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    #############
    #  WEAPONS  #
    #############

    # Get all weapons 

    def test_get_initial_weapons(self):
        assert get_weapon()["success"]

    # Create a weapon

    def test_create_weapon(self):
        body = create_weapon()
        weapon = body["data"]
        assert body["success"]
        assert weapon["name"] == SAMPLE_WEAPON["name"]
        assert weapon["atk"] == SAMPLE_WEAPON["atk"]

    def test_create_weapon_bad_request(self):
        bad_request_checker(SAMPLE_WEAPON, create_weapon, WEAPON_BAD_REQUEST)

    # Get a specific weapon

    def test_get_weapon(self):
        weapon_id = create_weapon()["data"]["id"]
        assert get_weapon(weapon_id)["success"]

    def test_get_invalid_weapon(self):
        body = get_weapon(100000, 404)
        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    # Delete a specific weapon

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

    # Create a battle

    def test_create_pvp_battle(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger = create_character(challenger_user_id)["data"]
        challenger_id = challenger["id"]
        opponent_user_id = create_user()["data"]["id"]
        opponent = create_character(opponent_user_id, sample_type=2)["data"]
        opponent_id = opponent["id"]
        pvp_battle = SAMPLE_BATTLE(challenger_id, opponent_id)

        body = create_battle(pvp_battle)
        battle = body["data"]
        assert body["success"]
        assert battle["challenger_id"] == pvp_battle["challenger_id"]
        assert battle["opponent_id"] == pvp_battle["opponent_id"]
        
        starting_log = battle["logs"][0]
        assert starting_log["challenger_hp"] == challenger["mhp"]
        assert starting_log["opponent_hp"] == opponent["mhp"]
        assert starting_log["action"] == LOG_STARTING_ACTION(challenger["name"], opponent["name"])

        assert battle["done"] == False

    def test_create_ai_battle(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger = create_character(challenger_user_id)["data"]
        challenger_id = challenger["id"]
        ai_battle = SAMPLE_BATTLE(challenger_id)

        body = create_battle(ai_battle)
        battle = body["data"]
        assert body["success"]
        assert battle["challenger_id"] == ai_battle["challenger_id"]
        assert battle["opponent_id"] == None
        
        starting_log = battle["logs"][0]
        assert starting_log["challenger_hp"] == challenger["mhp"]
        assert starting_log["opponent_hp"] == challenger["mhp"]
        assert starting_log["action"] == LOG_STARTING_ACTION(challenger["name"], "AI")

        assert battle["done"] == False

    def test_create_battle_bad_request(self):
        challenger_user_id = create_user()["data"]["id"]
        challenger_id = create_character(challenger_user_id)["data"]["id"]
        opponent_user_id = create_user()["data"]["id"]
        opponent_id = create_character(opponent_user_id, sample_type=2)["data"]["id"]
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

    # Get a specific battle

    def test_get_battle(self):
        battle_id = create_pvp_battle()["data"]["id"]
        assert get_battle(battle_id)["success"]

    def test_get_invalid_battle(self):
        body = get_battle(100000, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_NOT_FOUND

    # Delete a specific battle

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

    # Send battle action

    def test_send_battle_action(self):
        (_ , challenger_id), _, _, battle_id = respond_to_battle_request()
        challenger_action = SAMPLE_BATTLE_ACTION(challenger_id, "Attack")

        body = send_battle_action(battle_id, challenger_action)
        assert body["success"]
        assert body["data"] == BATTLE_ACTION_ACCEPTED

    ## Game logic tests START

    def test_challenger_wins(self):
        (challenger_uid, challenger_id), _, battle_id = execute_action_to_completion("Counter", "Attack")
        challenger = get_character(challenger_uid, challenger_id)["data"]
        done_battle = get_battle(battle_id)["data"]
        recent_log = most_recent_log(done_battle["logs"])
        assert recent_log["action"] == LOG_WINNER_ACTION(challenger["name"])
        assert challenger["mhp"] == MHP + MHP_INCREMENT
        assert challenger["atk"] == ATK + ATK_INCREMENT

    def test_opponent_wins(self):
        _, (opponent_uid, opponent_id), battle_id = execute_action_to_completion("Attack", "Counter")
        opponent = get_character(opponent_uid, opponent_id)["data"]
        done_battle = get_battle(battle_id)["data"]
        recent_log = most_recent_log(done_battle["logs"])
        assert recent_log["action"] == LOG_WINNER_ACTION(opponent["name"])
        assert opponent["mhp"] == MHP + MHP_INCREMENT
        assert opponent["atk"] == ATK + ATK_INCREMENT

    def test_battle_draw(self):
        _, _, battle_id = execute_action_to_completion("Attack", "Attack")
        done_battle = get_battle(battle_id)["data"]
        recent_log = most_recent_log(done_battle["logs"])
        assert recent_log["action"] == LOG_DRAW_ACTION

    def test_attack_attack_combo(self):
        c_name, c_act, c_atk, o_name, o_act, o_atk, log = execute_action("Attack", "Attack")
        assert log["challenger_hp"] == MHP - o_atk
        assert log["opponent_hp"] == MHP - c_atk
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, c_atk, o_name, o_act, o_atk)

    def test_attack_defend_combo(self):
        c_name, c_act, c_atk, o_name, o_act, _, log = execute_action("Attack", "Defend")
        assert log["challenger_hp"] == MHP
        assert log["opponent_hp"] == MHP - 0.5 * c_atk
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0.5 * c_atk, o_name, o_act, 0)

    def test_attack_counter_combo(self):
        c_name, c_act, c_atk, o_name, o_act, o_atk, log = execute_action("Attack", "Counter")
        assert log["challenger_hp"] == MHP - 2 * o_atk
        assert log["opponent_hp"] == MHP
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0, o_name, o_act, 2 * o_atk)

    def test_defend_attack_combo(self):
        c_name, c_act, _, o_name, o_act, o_atk, log = execute_action("Defend", "Attack")
        assert log["challenger_hp"] == MHP - 0.5 * o_atk
        assert log["opponent_hp"] == MHP
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0, o_name, o_act, 0.5 * o_atk)

    def test_defend_defend_combo(self):
        c_name, c_act, _, o_name, o_act, _, log = execute_action("Defend", "Defend")
        assert log["challenger_hp"] == MHP
        assert log["opponent_hp"] == MHP
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0, o_name, o_act, 0)

    def test_defend_counter_combo(self):
        c_name, c_act, c_atk, o_name, o_act, _, log = execute_action("Defend", "Counter")
        assert log["challenger_hp"] == MHP
        assert log["opponent_hp"] == MHP - c_atk
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, c_atk, o_name, o_act, 0)

    def test_counter_attack_combo(self):
        c_name, c_act, c_atk, o_name, o_act, _, log = execute_action("Counter", "Attack")
        assert log["challenger_hp"] == MHP
        assert log["opponent_hp"] == MHP - 2 * c_atk
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 2 * c_atk, o_name, o_act, 0)

    def test_counter_defend_combo(self):
        c_name, c_act, _, o_name, o_act, o_atk, log = execute_action("Counter", "Defend")
        assert log["challenger_hp"] == MHP - o_atk
        assert log["opponent_hp"] == MHP
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0, o_name, o_act, o_atk)

    def test_counter_counter_combo(self):
        c_name, c_act, _, o_name, o_act, _, log = execute_action("Counter", "Counter")
        assert log["challenger_hp"] == MHP
        assert log["opponent_hp"] == MHP
        assert log["action"] == LOG_DAMAGE_ACTION(c_name, c_act, 0, o_name, o_act, 0)

    ## Game logic tests END

    def test_send_battle_action_bad_request(self):
        (_, challenger_id), _, _, battle_id = respond_to_battle_request()
        sample = SAMPLE_BATTLE_ACTION(challenger_id, "Attack")
        wrapper = lambda data, code: send_battle_action(battle_id, data, code)
        bad_request_checker(sample, wrapper, BATTLE_ACTION_BAD_REQUEST)

    def test_send_battle_action_bad_request_action(self):
        (_, challenger_id), _, _, battle_id = respond_to_battle_request()
        challenger_action = SAMPLE_BATTLE_ACTION(challenger_id, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        body = send_battle_action(battle_id, challenger_action, 400)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_BAD_REQUEST_ACTION

    def test_send_battle_action_character_forbidden(self):
        _, _, _, battle_id = respond_to_battle_request()
        random_user_id = create_user()["data"]["id"]
        random_character_id = create_character(random_user_id)["data"]["id"]
        challenger_action = SAMPLE_BATTLE_ACTION(random_character_id, "Attack")

        body = send_battle_action(battle_id, challenger_action, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_CHARACTER_FORBIDDEN

    def test_send_battle_action_done_forbidden(self):
        (_, challenger_id), (_, opponent_id), battle_id = execute_action_to_completion("Attack", "Counter")
        
        challenger_action = SAMPLE_BATTLE_ACTION(challenger_id, "Counter")
        body = send_battle_action(battle_id, challenger_action, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_DONE_FORBIDDEN

        opponent_action = SAMPLE_BATTLE_ACTION(opponent_id, "Counter")
        body = send_battle_action(battle_id, opponent_action, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_DONE_FORBIDDEN
    
    def test_send_battle_action_already_forbidden(self):
        (_, challenger_id), _, _, battle_id = respond_to_battle_request()
        challenger_action = SAMPLE_BATTLE_ACTION(challenger_id, "Attack")
        send_battle_action(battle_id, challenger_action)

        body = send_battle_action(battle_id, challenger_action, 403)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_ALREADY_FORBIDDEN
    
    def test_send_battle_action_battle_not_found(self):
        (_, challenger_id), _, _, _ = respond_to_battle_request()
        challenger_action = SAMPLE_BATTLE_ACTION(challenger_id, "Attack")
        
        body = send_battle_action(100000, challenger_action, 404)
        assert not body["success"]
        assert body["error"] == BATTLE_ACTION_BATTLE_NOT_FOUND

    def test_send_battle_action_character_not_found(self):
        _, _, _, battle_id = respond_to_battle_request()
        challenger_action = SAMPLE_BATTLE_ACTION(100000, "Attack")

        body = send_battle_action(battle_id, challenger_action, 404)
        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND


    ##########
    #  LOGS  #
    ##########

    # Create a log for a battle

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
    
    # Get a battle’s log

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

    # Delete a battle’s log

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

    # Create a request

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
        sender = create_user()["data"]
        sender_id = sender["id"]
        receiver = create_user(sample_type=2)["data"]
        receiver_id = receiver["id"]
        request = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id))["data"]
        response = {"receiver_id": receiver_id, "accepted": True}
        respond_to_request(request["id"], response) # friendship established

        body = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id), 403)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_ALREADY_FORBIDDEN

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

    # Get a specific request

    def test_get_request(self):
        request_id = create_request(build_request("friend"))["data"]["id"] # input doesn't matter
        body = get_request(request_id)
        assert body["success"]

    def test_get_invalid_request(self):
        body = get_request(100000, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_NOT_FOUND

    # Delete a specific request

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

    # Respond to a specific request

    def test_respond_friend_request(self):
        sender = create_user()["data"]
        receiver = create_user(sample_type=2)["data"]
        request = create_request(SAMPLE_REQUEST("friend", sender["id"], receiver["id"]))["data"]
        response = SAMPLE_RESPONSE(receiver["id"], True)

        body = respond_to_request(request["id"], response)
        user = body["data"]
        assert body["success"]
        assert user["id"] == receiver["id"]
        assert user["username"] == receiver["username"]
        assert user["characters"] == receiver["characters"]
        
        new_friend = user["friends"][0]
        assert new_friend["id"] == sender["id"]
        assert new_friend["username"] == sender["username"]
        assert new_friend["characters"] == sender["characters"]

        sender = get_user(sender["id"])["data"]
        assert sender["friends"][0]["id"] == receiver["id"] # ensure sender also friends

    def test_respond_battle_request(self):
        sending_user_id = create_user()["data"]["id"]
        sender = create_character(sending_user_id)["data"]
        receiving_user_id = create_user()["data"]["id"]
        receiver = create_character(receiving_user_id, sample_type=2)["data"]
        request = create_request(SAMPLE_REQUEST("battle", sender["id"], receiver["id"]))["data"]
        response = SAMPLE_RESPONSE(receiver["id"], True)

        body = respond_to_request(request["id"], response)
        battle = body["data"]
        assert body["success"]
        assert battle["challenger_id"] == sender["id"]
        assert battle["opponent_id"] == receiver["id"]

        starting_log = battle["logs"][0]
        assert starting_log["challenger_hp"] == sender["mhp"]
        assert starting_log["opponent_hp"] == receiver["mhp"]
        assert starting_log["action"] == LOG_STARTING_ACTION(sender["name"], receiver["name"])
        assert battle["done"] == False

    def test_respond_deny_request(self):
        sending_user = create_user()["data"]
        sending_character = create_character(sending_user["id"])["data"]
        receiving_user = create_user(sample_type=2)["data"]
        receiving_character = create_character(receiving_user["id"], sample_type=2)["data"]
        friend_request = create_request(SAMPLE_REQUEST("friend", sending_user["id"], 
                                                        receiving_user["id"]))["data"]
        friend_response = SAMPLE_RESPONSE(receiving_user["id"], False)

        body = respond_to_request(friend_request["id"], friend_response)
        assert body["success"]
        assert body["data"] == REQUEST_RESPOND_DENIED(sending_user["username"], "friend")

        battle_request = create_request(SAMPLE_REQUEST("battle", sending_character["id"], 
                                                        receiving_character["id"]))["data"]
        battle_response = SAMPLE_RESPONSE(receiving_character["id"], False)

        body = respond_to_request(battle_request["id"], battle_response)
        assert body["success"]
        assert body["data"] == REQUEST_RESPOND_DENIED(sending_character["name"], "battle")

    def test_respond_request_bad_request(self):
        request = create_request(build_request("friend"))["data"] # type doesn't matter
        wrapper = lambda data, code: respond_to_request(request["id"], data, code)
        response = SAMPLE_RESPONSE(request["receiver_id"], True) # accepted doesn't matter
        bad_request_checker(response, wrapper, REQUEST_RESPOND_BAD_REQUEST)

    def test_respond_request_forbidden_own(self):
        sender_id = create_user()["data"]["id"]
        receiver_id = create_user()["data"]["id"]
        request = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id))["data"]
        response = SAMPLE_RESPONSE(sender_id, True)
        body = respond_to_request(request["id"], response, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_RESPOND_FORBIDDEN_OWN

    def test_respond_request_forbidden_anothers(self):
        request = create_request(build_request("friend"))["data"]
        outsider_id = create_user()["data"]["id"]
        response = SAMPLE_RESPONSE(outsider_id, True)
        body = respond_to_request(request["id"], response, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_RESPOND_FORBIDDEN_ANOTHERS

    def test_respond_request_forbidden_accepted(self):
        sender_id = create_user()["data"]["id"]
        receiver_id = create_user()["data"]["id"]
        request = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id))["data"]
        response = SAMPLE_RESPONSE(receiver_id, True)
        respond_to_request(request["id"], response)

        body = respond_to_request(request["id"], response, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_RESPOND_FORBIDDEN_ACCEPTED

    def test_respond_request_forbidden_denied(self):
        sender_id = create_user()["data"]["id"]
        receiver_id = create_user()["data"]["id"]
        request = create_request(SAMPLE_REQUEST("friend", sender_id, receiver_id))["data"]
        response = SAMPLE_RESPONSE(receiver_id, False)
        respond_to_request(request["id"], response)

        body = respond_to_request(request["id"], response, 403)
        assert not body["success"]
        assert body["error"] == REQUEST_RESPOND_FORBIDDEN_DENIED
    
    def test_respond_request_not_found(self):
        request = create_request(build_request("friend"))["data"]
        response = SAMPLE_RESPONSE(request["receiver_id"], True)
        body = respond_to_request(100000, response, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_NOT_FOUND

    def test_respond_friend_request_user_not_found(self):
        request = create_request(build_request("friend"))["data"]
        response = SAMPLE_RESPONSE(100000, True)
        body = respond_to_request(request["id"], response, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_FRIEND_RECEIVER_NOT_FOUND

    def test_respond_battle_request_character_not_found(self):
        request = create_request(build_request("battle"))["data"]
        response = SAMPLE_RESPONSE(100000, True)
        body = respond_to_request(request["id"], response, 404)
        assert not body["success"]
        assert body["error"] == REQUEST_BATTLE_RECEIVER_NOT_FOUND

    

def run_tests():
    sleep(1.5)
    unittest.main()

if __name__ == "__main__":
    thread = Thread(target=run_tests)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
