from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

friends_table = db.Table("association", db.Model.metadata,
  db.Column("friender_id", db.Integer, db.ForeignKey("user.id")),
  db.Column("friendee_id", db.Integer, db.ForeignKey("user.id"))
  )

class User(db.Model):
  __tablename__ = "user"
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String, nullable=False)
  characters = db.relationship('Character', cascade="delete")
  friends = db.relationship('User', secondary=friends_table, 
                            primaryjoin=id==friends_table.c.friender_id,
                            secondaryjoin=id==friends_table.c.friendee_id)

  def __init__(self, **kwargs):
    self.username = kwargs.get("username", "")
    self.characters = []
    self.friends = []

  def serialize(self):
    return {
      "id": self.id,
      "username": self.username,
      "characters": [character.serialize() for character in self.characters],
      "friends": [friend.serialize_friendless() for friend in self.friends]
    }
  
  def serialize_friendless(self):
    return {
      "id": self.id,
      "username": self.username,
      "characters": [character.serialize() for character in self.characters],
    }

class Character(db.Model):
  __tablename__ = "character"
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  mhp = db.Column(db.Integer, nullable=False)
  atk = db.Column(db.Integer, nullable=False)
  weapon_id = db.Column(db.Integer, db.ForeignKey("weapon.id"))
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

  def __init__(self, **kwargs):
    self.name = kwargs.get("name", "")
    self.mhp = 10
    self.atk = 2
    self.weapon_id = None
    self.user_id = kwargs.get("uid", 0)

  def serialize(self):
    return {
      "id": self.id,
      "name": self.name,
      "mhp": self.mhp,
      "atk": self.atk,
      "equipped": self.get_weapon()
    }
  
  def get_weapon(self):
    weapon = Weapon.query.filter_by(id=self.weapon_id).first()
    if weapon is None:
      return None
    return weapon.serialize()

class Weapon(db.Model):
  __tablename__ = "weapon"
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String, nullable=False)
  atk = db.Column(db.Integer, nullable=False)

  def __init__(self, **kwargs):
    self.name = kwargs.get("name", "")
    atk = kwargs.get("atk", 1)
    self.atk = 1 if atk < 1 else atk

  def serialize(self):
    return {
      "id": self.id,
      "name": self.name,
      "atk": self.atk
    }

class Battle(db.Model):
  __tablename__ = "battle"
  id = db.Column(db.Integer, primary_key=True)
  challenger_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
  opponent_id = db.Column(db.Integer, db.ForeignKey("character.id"))
  logs = db.relationship('Log', cascade="delete")
  action = db.relationship('Action', cascade="delete")
  done = db.Column(db.Boolean, nullable=False)

  def __init__(self, **kwargs):
    self.challenger_id = kwargs.get("challenger_id", 0)
    self.opponent_id = kwargs.get("opponent_id", None)
    self.logs = []
    self.action = [] # one element list
    self.done = False

  def serialize(self):
    return {
      "id": self.id,
      "challenger_id": self.challenger_id,
      "opponent_id": self.opponent_id,
      "logs": [log.serialize() for log in self.logs],
      "done": self.done
    }

class Log(db.Model):
  __tablename__ = "log"
  id = db.Column(db.Integer, primary_key=True)
  timestamp = db.Column(db.Integer, nullable=False)
  challenger_hp = db.Column(db.Integer, nullable=False)
  opponent_hp = db.Column(db.Integer, nullable=False)
  action = db.Column(db.String, nullable=False)
  battle_id = db.Column(db.Integer, db.ForeignKey("battle.id"), nullable=False)

  def __init__(self, **kwargs):
    self.timestamp = kwargs.get("timestamp", 0)
    self.challenger_hp = kwargs.get("challenger_hp", 0)
    self.opponent_hp = kwargs.get("opponent_hp", 0)
    self.action = kwargs.get("action", "")
    self.battle_id = kwargs.get("bid", 0)

  def serialize(self):
    return {
      "id": self.id,
      "timestamp": self.timestamp,
      "challenger_hp": self.challenger_hp,
      "opponent_hp": self.opponent_hp,
      "action": self.action
    }

class Request(db.Model):
  __tablename__ = "request"
  id = db.Column(db.Integer, primary_key=True)
  kind = db.Column(db.String, nullable=False)
  user_sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
  user_receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"))
  character_sender_id = db.Column(db.Integer, db.ForeignKey("character.id"))
  character_receiver_id = db.Column(db.Integer, db.ForeignKey("character.id"))
  accepted = db.Column(db.Boolean)

  def __init__(self, **kwargs):
    self.kind = kwargs.get("kind", "")
    if self.kind == "friend":
      self.user_sender_id = kwargs.get("sender_id", 0)
      self.user_receiver_id = kwargs.get("receiver_id", 0)
    elif self.kind == "battle":
      self.character_sender_id = kwargs.get("sender_id", 0)
      self.character_receiver_id = kwargs.get("receiver_id", 0)
    self.accepted = None

  def __get_id(self, of):
    if of == "sender":
      return self.user_sender_id if self.kind == "friend" else self.character_sender_id
    elif of == "receiver":
      return self.user_receiver_id if self.kind == "friend" else self.character_receiver_id

  def serialize(self):
    return {
      "id": self.id,
      "kind": self.kind,
      "sender_id": self.__get_id(of="sender"),
      "receiver_id": self.__get_id(of="receiver"),
      "accepted": self.accepted
    }

class Action(db.Model):
  __tablename__ = "action"
  id = db.Column(db.Integer, primary_key=True)
  challenger_action = db.Column(db.String)
  opponent_action = db.Column(db.String)
  battle_id = db.Column(db.Integer, db.ForeignKey("battle.id"))

  def __init__(self, **kwargs):
    self.battle_id = kwargs.get("bid", 0) 


