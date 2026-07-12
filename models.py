from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


db = SQLAlchemy()

hunt_monsters = db.Table(
    "hunt_monsters",
    db.Column("hunt_id", db.Integer, db.ForeignKey("hunts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("monster_id", db.Integer, db.ForeignKey("monsters.id", ondelete="CASCADE"), primary_key=True),
)

hunt_charms = db.Table(
    "hunt_charms",
    db.Column("hunt_id", db.Integer, db.ForeignKey("hunts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("charm_id", db.Integer, db.ForeignKey("charms.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin")
    active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime)

    @property
    def is_admin(self):
        return self.role == "admin" and self.active


class Monster(TimestampMixin, db.Model):
    __tablename__ = "monsters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    experience = db.Column(db.Integer, nullable=False, default=0)
    life = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(600))
    weaknesses = db.Column(db.JSON, nullable=False, default=list)
    attacks = db.Column(db.JSON, nullable=False, default=list)


class Charm(TimestampMixin, db.Model):
    __tablename__ = "charms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(600))


class Hunt(TimestampMixin, db.Model):
    __tablename__ = "hunts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    location = db.Column(db.String(250), nullable=False)
    protections = db.Column(db.JSON, nullable=False, default=list)
    weaknesses = db.Column(db.JSON, nullable=False, default=list)
    monsters = db.relationship("Monster", secondary=hunt_monsters, lazy="selectin")
    charms = db.relationship("Charm", secondary=hunt_charms, lazy="selectin")
    monster_charm_assignments = db.relationship(
        "HuntMonsterCharm",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="HuntMonsterCharm.priority.desc()",
    )


class HuntMonsterCharm(TimestampMixin, db.Model):
    __tablename__ = "hunt_monster_charms"

    id = db.Column(db.Integer, primary_key=True)
    hunt_id = db.Column(db.Integer, db.ForeignKey("hunts.id", ondelete="CASCADE"), nullable=False, index=True)
    monster_id = db.Column(db.Integer, db.ForeignKey("monsters.id", ondelete="CASCADE"), nullable=False, index=True)
    major_charm_id = db.Column(db.Integer, db.ForeignKey("charms.id", ondelete="SET NULL"))
    minor_charm_id = db.Column(db.Integer, db.ForeignKey("charms.id", ondelete="SET NULL"))
    priority = db.Column(db.Integer, nullable=False, default=3)

    monster = db.relationship("Monster", lazy="joined")
    major_charm = db.relationship("Charm", foreign_keys=[major_charm_id], lazy="joined")
    minor_charm = db.relationship("Charm", foreign_keys=[minor_charm_id], lazy="joined")

    __table_args__ = (
        UniqueConstraint("hunt_id", "monster_id", name="uq_hunt_monster_charm"),
    )


class Imbuement(TimestampMixin, db.Model):
    __tablename__ = "imbuements"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    items = db.relationship("ImbuementItem", cascade="all, delete-orphan", backref="imbuement", lazy="selectin")
    __table_args__ = (UniqueConstraint("name", "level", name="uq_imbuement_name_level"),)


class ImbuementItem(db.Model):
    __tablename__ = "imbuement_items"
    id = db.Column(db.Integer, primary_key=True)
    imbuement_id = db.Column(db.Integer, db.ForeignKey("imbuements.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    image_url = db.Column(db.String(600))
