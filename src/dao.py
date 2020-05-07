from db import db, User, Character, Weapon, Battle, Log, Request
import time

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

def end_friendship(uid, ex_friend_id):
  ending_user = User.query.filter_by(id=uid).first()
  if ending_user is None:
    return "The provided un-friender does not exist!", 404

  ex_friend_user = User.query.filter_by(id=ex_friend_id).first()
  if ex_friend_user is None:
    return "The provided ex-friend does not exist!", 404

  if uid == ex_friend_id:
    return "You can never unfriend yourself!", 403
  
  if ex_friend_user not in ending_user.friends:
    return "You aren’t friends with this user!", 403

  ending_user.friends.remove(ex_friend_user)
  ex_friend_user.friends.remove(ending_user)
  db.session.commit()
  return ex_friend_user.serialize(), 202

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

  new_battle = Battle(
    challenger_id=challenger_id,
    opponent_id=opponent_id
  )
  db.session.add(new_battle)
  db.session.commit()

  # Adding the starter log
  starting_log = create_starter_log(challenger, opponent, new_battle.id)
  return add_log(starting_log, new_battle.id), 201

def is_battling(cid):
  first_check = Battle.query.filter_by(challenger_id=cid, 
                                      done=False).first()
  second_check = Battle.query.filter_by(opponent_id=cid, 
                                      done=False).first()
  return (first_check is not None) or (second_check is not None)

def add_log(log, bid):
  battle = Battle.query.filter_by(id=bid).first()
  battle.logs.insert(0, log)

  db.session.commit()
  return battle.serialize()

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
  return new_log

def create_starter_log(challenger, opponent, bid):
  opponent_name = "AI" if opponent is None else opponent.name
  action = f"The battle between Challenger {challenger.name} and Opponent {opponent_name} has begun."
  opponent_mhp = challenger.mhp if opponent is None else opponent.mhp
  return create_log(
    timestamp=time.time_ns(),
    challenger_hp=challenger.mhp,
    opponent_hp=opponent_mhp,
    action=action,
    bid=bid
  )

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

##############
#  REQUESTS  #
##############

def create_request(kind, sender_id, receiver_id):
  if kind == "friend":
    sender = User.query.filter_by(id=sender_id).first()
    if sender is None:
      return "The sending user does not exist!", 404

    receiver = User.query.filter_by(id=receiver_id).first()
    if receiver is None:
      return "The receiving user does not exist!", 404
    
    if sender_id == receiver_id:
      return "You can’t send a friend request to yourself!", 403

    if check_friend_pending(sender_id, receiver_id):
      return "There is already a pending friend request between these users!", 403

    if receiver in sender.friends:
      return "You are already friends!", 403

  elif kind == "battle":
    sender = Character.query.filter_by(id=sender_id).first()
    if sender is None:
      return "The sending character does not exist!", 404

    receiver = Character.query.filter_by(id=receiver_id).first()
    if receiver is None:
      return "The receiving character does not exist!", 404

    if check_battle_pending(sender_id, receiver_id):
      return "There is already a pending battle request between these characters!", 403

    if is_battling(sender_id):
      return "The sender is already in a battle!", 403

    if is_battling(receiver_id):
      return "The receiver is already in a battle!", 403

    if sender.user_id == receiver.user_id:
      return "The provided characters belong to the same user!", 403

  new_request = Request(
    kind=kind,
    sender_id=sender_id,
    receiver_id=receiver_id
  )

  db.session.add(new_request)
  db.session.commit()
  return new_request.serialize(), 201

def check_friend_pending(first_id, second_id):
  request_one = Request.query.filter_by(user_sender_id=first_id, 
                                        user_receiver_id=second_id,
                                        accepted=None).first()
  request_two = Request.query.filter_by(user_sender_id=second_id, 
                                        user_receiver_id=first_id,
                                        accepted=None).first()
  return request_one is not None or request_two is not None

def check_battle_pending(first_id, second_id):
  request_one = Request.query.filter_by(character_sender_id=first_id, 
                                        character_receiver_id=second_id,
                                        accepted=None).first()
  request_two = Request.query.filter_by(character_sender_id=second_id, 
                                        character_receiver_id=first_id,
                                        accepted=None).first()
  return request_one is not None or request_two is not None
  
def get_request(rid):
  return validate_request_request(rid, delete=False)

def delete_request(rid):
  return validate_request_request(rid, delete=True)

def validate_request_request(rid, delete):
  req = Request.query.filter_by(id=rid).first()
  if req is None:
    return None
  
  if delete:
    db.session.delete(req)
    db.session.commit()
  return req.serialize()

def respond_to_request(rid, receiver_id, accepted):
  request = Request.query.filter_by(id=rid).first()
  if request is None:
    return "This request does not exist!", 404
  
  receiver = (User.query.filter_by(id=receiver_id).first() if request.kind == "friend" 
              else Character.query.filter_by(id=receiver_id).first())
  if receiver is None:
    return ("The receiving user does not exist!" if request.kind == "friend" else
            "The receiving character does not exist!"), 404
  
  if get_request_id("sender", request) == receiver_id:
    return "You can’t respond to your own request!", 403

  if get_request_id("receiver", request) != receiver_id:
    return "This request was not sent to you!", 403

  if request.accepted is not None:
    status = "accepted!" if request.accepted else "denied!"
    return f"This request has already been {status}", 403

  sender = (User.query.filter_by(id=request.user_sender_id).first() if request.kind == "friend" 
            else Character.query.filter_by(id=request.character_sender_id).first())
  
  if not accepted:
    sender_name = sender.username if request.kind == "friend" else sender.name
    response = f"You have rejected {sender_name}’s {request.kind} request"
  else:
    if request.kind == "friend":
      receiver.friends.append(sender)
      sender.friends.append(receiver)
      response = receiver.serialize()
    elif request.kind == "battle":
      battle, _ = create_battle(request.character_sender_id, receiver_id)
      response = battle.serialize()
  
  request.accepted = accepted
  db.session.commit()
  return response, 202


def get_request_id(of, request):
  if request.kind == "friend":
    if of == "sender":
      return request.user_sender_id
    elif of == "receiver":
      return request.user_receiver_id
  elif request.kind == "battle":
    if of == "sender":
      return request.character_sender_id
    elif of == "receiver":
      return request.character_receiver_id
  
  