from db import db, User, Character, Weapon

###########
#  USERS  #
###########

def get_all_users():
  return [user.serialize() for user in User.query.all()]

def create_user(username):
  new_user = User(
    username=username
  )

  db.session.add(new_user)
  db.session.commit()
  return new_user.serialize()

def get_user(uid):
  return validate_user_request(uid, delete=False)

def delete_user(uid):
  return validate_user_request(uid, delete=True)

def validate_user_request(uid, delete):
  user = User.query.filter_by(id=uid).first()
  if user is None:
    return None
  
  if delete:
    db.session.delete(user)
    db.session.commit()
  return user.serialize()

################
#  CHARACTERS  #
################

def create_character(name, uid):
  if get_user(uid) is None:
    return None

  new_character = Character(
    name=name,
    uid=uid
  )

  db.session.add(new_character)
  db.session.commit()
  return new_character.serialize()

def get_character(uid, cid):
  return validate_character_request(uid, cid, delete=False)

def delete_character(uid, cid):
  return validate_character_request(uid, cid, delete=True)

def validate_character_request(uid, cid, delete):
  user = get_user(uid)
  if user is None:
    return "The provided user does not exist!", 404
  
  character = Character.query.filter_by(id=cid).first()
  if character is None:
    return "This character does not exist!", 404
  
  serialized_character = character.serialize()
  if serialized_character not in user["characters"]:
    return "This character does not belong to the provided user!", 403

  if delete:
    db.session.delete(character)
    db.session.commit()
  return serialized_character, 200

#############
#  WEAPONS  #
#############

def get_all_weapons():
  return [weapon.serialize() for weapon in Weapon.query.all()]

def create_weapon(name, atk):
  new_weapon = Weapon(
    name=name,
    atk=atk
  )

  db.session.add(new_weapon)
  db.session.commit()
  return new_weapon.serialize()

def get_weapon(wid):
  return validate_weapon_request(wid, delete=False)

def delete_weapon(wid):
  return validate_weapon_request(wid, delete=True)

def validate_weapon_request(wid, delete):
  weapon = Weapon.query.filter_by(id=wid).first()
  if weapon is None:
    return None
  
  if delete:
    db.session.delete(weapon)
    db.session.commit()
  return weapon.serialize()