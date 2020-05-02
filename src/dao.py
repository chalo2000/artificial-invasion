from db import db, User, Character, Weapon, Battle, Log

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
    return serialized_character, 202
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

#############
#  BATTLES  #
#############

def create_battle(challenger_id, opponent_id):
  challenger = Character.query.filter_by(id=challenger_id).first()
  if challenger is None:
    return "The challenger character does not exist!", 404

  opponent = Character.query.filter_by(id=opponent_id).first()
  if opponent_id is not None and opponent is None:
    return "The opponent character does not exist!", 404
  
  if opponent_id is not None and challenger.user_id == opponent.user_id:
    return "The challenger and opponent belong to the same user!", 403
    
  if is_battling(challenger_id):
    return "The challenger is already in a battle!", 403

  if opponent_id is not None and is_battling(opponent_id):
    return "The opponent is already in a battle!", 403

  if request_pending(challenger_id, opponent_id):
    return "There is already a battle request pending!", 403

  new_battle = Battle(
    challenger_id=challenger_id,
    opponent_id=opponent_id
  )

  db.session.add(new_battle)
  db.session.commit()
  return new_battle.serialize(), 201

def is_battling(cid):
  first_check = Battle.query.filter_by(challenger_id=cid, 
                                      started=True).first()
  second_check = Battle.query.filter_by(opponent_id=cid, 
                                      started=True).first()
  return (first_check is not None) or (second_check is not None)

def request_pending(challenger_id, opponent_id):
  first_check = Battle.query.filter_by(challenger_id=challenger_id, 
                                      opponent_id=opponent_id).first()
  second_check = Battle.query.filter_by(challenger_id=opponent_id, 
                                      opponent_id=challenger_id).first()
  return (first_check is not None) or (second_check is not None)

def get_battle(bid):
  return validate_battle_request(bid, delete=False)

def delete_battle(bid):
  return validate_battle_request(bid, delete=True)

def validate_battle_request(bid, delete):
  battle = Battle.query.filter_by(id=bid).first()
  if battle is None:
    return None
  
  if delete:
    db.session.delete(battle)
    db.session.commit()
  return battle.serialize()

##########
#  LOGS  #
##########

def create_log(timestamp, challenger_hp, opponent_hp, action, bid):
  if get_battle(bid) is None:
    return None

  new_log = Log(
    timestamp=timestamp,
    challenger_hp=challenger_hp,
    opponent_hp=opponent_hp,
    action=action,
    bid=bid
  )

  db.session.add(new_log)
  db.session.commit()
  return new_log.serialize()

def get_log(bid, lid):
  return validate_log_request(bid, lid, delete=False)

def delete_log(bid, lid):
  return validate_log_request(bid, lid, delete=True)

def validate_log_request(bid, lid, delete):
  battle = get_battle(bid)
  if battle is None:
    return "The provided battle does not exist!", 404
  
  log = Log.query.filter_by(id=lid).first()
  if log is None:
    return "This log does not exist!", 404
  
  serialized_log = log.serialize()
  if serialized_log not in battle["logs"]:
    return "This log does not belong to the provided battle!", 403

  if delete:
    db.session.delete(log)
    db.session.commit()
    return serialized_log, 202
  return serialized_log, 200