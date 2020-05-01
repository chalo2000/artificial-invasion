import unittest
import json
import requests
from app import app
from threading import Thread
from time import sleep

# URL pointing to your local dev host
LOCAL_URL = "http://localhost:5000"

# Sample request bodies
SAMPLE_USER = {"username": "chalo2000"}
SAMPLE_CHARACTER = {"name": "Chalos"}
SAMPLE_WEAPON = {"name": "Rubber Duck", "atk": 1337}

# API Documentation error messages
USER_BAD_REQUEST = "Provide a proper request of the form {username: string}"
USER_NOT_FOUND = "This user does not exist!"
CHARACTER_BAD_REQUEST = "Provide a proper request of the form {name: string}"
CHARACTER_FORBIDDEN = "This character does not belong to the provided user!"
CHARACTER_USER_NOT_FOUND = "The provided user does not exist!"
CHARACTER_NOT_FOUND = "This character does not exist!"
WEAPON_BAD_REQUEST = 'Provide a proper request of the form {name: string, atk: number}'
WEAPON_NOT_FOUND = "This weapon does not exist!"

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
    def test_get_initial_users(self):
        res = requests.get(gen_users_path())
        assert res.status_code == 200
        body = unwrap_response(res)
        assert body["success"]
    
    def test_create_user(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user = body["data"]

        assert body["success"]
        assert user["username"] == SAMPLE_USER["username"]
        assert user["characters"] == []

    def test_create_user_bad_request(self):
        # Test incorrect field name
        res = requests.post(gen_users_path(), data=json.dumps({"beep": "Chalos"}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == USER_BAD_REQUEST

        # Test incorrect field type
        res = requests.post(gen_users_path(), data=json.dumps({"username": 0}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == USER_BAD_REQUEST

    def test_get_user(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.get(gen_users_path(user_id))
        assert res.status_code == 200
        body = unwrap_response(res)

        assert body["success"]

    def test_get_invalid_user(self):
        res = requests.get(gen_users_path(1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND

    def test_delete_user(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.delete(gen_users_path(user_id))
        assert res.status_code == 202
        body = unwrap_response(res)

        assert body["success"]

        res = requests.get(gen_users_path(user_id))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND

    def test_delete_invalid_user(self):
        res = requests.delete(gen_users_path(1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == USER_NOT_FOUND
    
    def test_create_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.post(gen_characters_path(user_id), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 201
        body = unwrap_response(res)
        character = body["data"]

        assert body["success"]
        assert character["name"] == SAMPLE_CHARACTER["name"]
        assert character["mhp"] == 10
        assert character["atk"] == 2
        assert character["equipped"] == None

    def test_create_character_bad_request(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        # Test incorrect field name
        res = requests.post(gen_characters_path(user_id), data=json.dumps({"boop": "Chalos"}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == CHARACTER_BAD_REQUEST

        # Test incorrect field type
        res = requests.post(gen_characters_path(user_id), data=json.dumps({"name": 0}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == CHARACTER_BAD_REQUEST

    def test_create_character_invalid_user(self):
        res = requests.post(gen_characters_path(1000), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 404
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND
    
    def test_get_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.post(gen_characters_path(user_id), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 201
        body = unwrap_response(res)
        character_id = body["data"]["id"]

        res = requests.get(gen_characters_path(user_id, character_id))
        assert res.status_code == 200
        body = unwrap_response(res)

        assert body["success"]

        character = body["data"]

        assert character["name"] == SAMPLE_CHARACTER["name"]
        assert character["mhp"] == 10
        assert character["atk"] == 2
        assert character["equipped"] == None

    def test_get_forbidden_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        first_user_id = body["data"]["id"]

        res = requests.post(gen_characters_path(first_user_id), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 201
        body = unwrap_response(res)
        character_id = body["data"]["id"]

        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        second_user_id = body["data"]["id"]

        res = requests.get(gen_characters_path(second_user_id, character_id))
        assert res.status_code == 403
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

    def test_get_character_invalid_user(self):
        res = requests.get(gen_characters_path(1000, 0))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND

    def test_get_invalid_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.get(gen_characters_path(user_id, 1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_delete_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.post(gen_characters_path(user_id), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 201
        body = unwrap_response(res)
        character_id = body["data"]["id"]

        res = requests.delete(gen_characters_path(user_id, character_id))
        assert res.status_code == 202
        body = unwrap_response(res)

        assert body["success"]

        res = requests.get(gen_characters_path(user_id, character_id))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_delete_forbidden_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        first_user_id = body["data"]["id"]

        res = requests.post(gen_characters_path(first_user_id), data=json.dumps(SAMPLE_CHARACTER))
        assert res.status_code == 201
        body = unwrap_response(res)
        character_id = body["data"]["id"]

        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        second_user_id = body["data"]["id"]

        res = requests.delete(gen_characters_path(second_user_id, character_id))
        assert res.status_code == 403
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_FORBIDDEN

    def test_delete_character_invalid_user(self):
        res = requests.delete(gen_characters_path(1000, 0))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_USER_NOT_FOUND

    def test_delete_invalid_character(self):
        res = requests.post(gen_users_path(), data=json.dumps(SAMPLE_USER))
        assert res.status_code == 201
        body = unwrap_response(res)
        user_id = body["data"]["id"]

        res = requests.delete(gen_characters_path(user_id, 1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == CHARACTER_NOT_FOUND

    def test_get_initial_weapons(self):
        res = requests.get(gen_weapons_path())
        assert res.status_code == 200
        body = unwrap_response(res)
        assert body["success"]

    def test_create_weapon(self):
        res = requests.post(gen_weapons_path(), data=json.dumps(SAMPLE_WEAPON))
        assert res.status_code == 201
        body = unwrap_response(res)
        weapon = body["data"]

        assert body["success"]
        assert weapon["name"] == SAMPLE_WEAPON["name"]
        assert weapon["atk"] == SAMPLE_WEAPON["atk"]

    def test_create_weapon_bad_request(self):
        # Test incorrect field names
        res = requests.post(gen_weapons_path(), data=json.dumps({"ding": "dong", "atk": 5}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == WEAPON_BAD_REQUEST

        res = requests.post(gen_weapons_path(), data=json.dumps({"name": "dong", "dong": 5}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == WEAPON_BAD_REQUEST

        # Test incorrect field types
        res = requests.post(gen_weapons_path(), data=json.dumps({"name": 0, "atk": 0}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == WEAPON_BAD_REQUEST

        res = requests.post(gen_weapons_path(), data=json.dumps({"name": "0", "atk": "0"}))
        assert res.status_code == 400
        body = unwrap_response(res)
        assert not body["success"]
        assert body["error"] == WEAPON_BAD_REQUEST

    def test_get_weapon(self):
        res = requests.post(gen_weapons_path(), data=json.dumps(SAMPLE_WEAPON))
        assert res.status_code == 201
        body = unwrap_response(res)
        weapon_id = body["data"]["id"]

        res = requests.get(gen_weapons_path(weapon_id))
        assert res.status_code == 200
        body = unwrap_response(res)

        assert body["success"]

    def test_get_invalid_weapon(self):
        res = requests.get(gen_weapons_path(1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    def test_delete_weapon(self):
        res = requests.post(gen_weapons_path(), data=json.dumps(SAMPLE_WEAPON))
        assert res.status_code == 201
        body = unwrap_response(res)
        weapon_id = body["data"]["id"]

        res = requests.delete(gen_weapons_path(weapon_id))
        assert res.status_code == 202
        body = unwrap_response(res)

        assert body["success"]

        res = requests.get(gen_weapons_path(weapon_id))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

    def test_delete_invalid_weapon(self):
        res = requests.delete(gen_weapons_path(1000))
        assert res.status_code == 404
        body = unwrap_response(res)

        assert not body["success"]
        assert body["error"] == WEAPON_NOT_FOUND

def run_tests():
    sleep(1.5)
    unittest.main()

if __name__ == "__main__":
    thread = Thread(target=run_tests)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
