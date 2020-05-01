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
                            secondaryjoin=id==friends_table.c.friendee_id,
                            back_populates="friends")

  def __init__(self, **kwargs):
    self.username = kwargs.get("username", "")
    self.characters = []

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
    self.user_id = kwargs.get("uid", "")

  def serialize(self):
    return {
      "id": self.id,
      "name": self.name,
      "mhp": self.mhp,
      "atk": self.atk,
      "equipped": self.weapon_id
    }

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