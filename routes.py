import os
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_
from models import Charm, Hunt, Imbuement, ImbuementItem, Monster, db
from app import ELEMENTS
from auth import admin_required
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("main", __name__)
LEVEL_ITEM_COUNT = {"Basic": 1, "Intricate": 2, "Powerful": 3}


def _search_term():
    return request.args.get("q", "").strip()


def _element_values(prefix, with_value=True):
    values = []
    for element in ELEMENTS:
        key = element.lower().replace(" ", "_")
        enabled = request.form.get(f"{prefix}_{key}") == "on"
        raw_value = request.form.get(f"{prefix}_{key}_value", "").strip()
        if enabled:
            entry = {"element": element}
            if with_value:
                try:
                    entry["value"] = int(raw_value or 0)
                except ValueError:
                    entry["value"] = 0
            values.append(entry)
    return values


@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("main.admin_panel"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        expected_user = os.getenv("ADMIN_USERNAME", "admin")
        password_hash = os.getenv("ADMIN_PASSWORD_HASH")
        expected_password = os.getenv("ADMIN_PASSWORD", "admin123")
        valid_password = check_password_hash(password_hash, password) if password_hash else password == expected_password
        if username == expected_user and valid_password:
            session.clear()
            session["is_admin"] = True
            session["admin_username"] = username
            flash("Login realizado com sucesso.", "success")
            next_url = request.args.get("next")
            return redirect(next_url if next_url and next_url.startswith("/") else url_for("main.admin_panel"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("admin/login.html")


@bp.get("/admin")
@admin_required
def admin_panel():
    stats = {
        "monsters": db.session.scalar(db.select(func.count()).select_from(Monster)),
        "charms": db.session.scalar(db.select(func.count()).select_from(Charm)),
        "hunts": db.session.scalar(db.select(func.count()).select_from(Hunt)),
        "imbuements": db.session.scalar(db.select(func.count()).select_from(Imbuement)),
    }
    return render_template("admin/panel.html", stats=stats)


@bp.post("/admin/logout")
def admin_logout():
    session.clear()
    flash("Você saiu da área administrativa.", "success")
    return redirect(url_for("main.dashboard"))


@bp.get("/")
def dashboard():
    stats = {
        "monsters": db.session.scalar(db.select(func.count()).select_from(Monster)),
        "charms": db.session.scalar(db.select(func.count()).select_from(Charm)),
        "hunts": db.session.scalar(db.select(func.count()).select_from(Hunt)),
        "imbuements": db.session.scalar(db.select(func.count()).select_from(Imbuement)),
    }
    latest_hunts = db.session.scalars(db.select(Hunt).order_by(Hunt.created_at.desc()).limit(4)).all()
    return render_template("dashboard.html", stats=stats, latest_hunts=latest_hunts)


@bp.route("/monsters")
def monsters_list():
    q = _search_term()
    stmt = db.select(Monster)
    if q:
        stmt = stmt.where(Monster.name.ilike(f"%{q}%"))
    monsters = db.session.scalars(stmt.order_by(Monster.name)).all()
    return render_template("monsters/list.html", monsters=monsters, q=q)


@bp.route("/monsters/new", methods=["GET", "POST"])
@bp.route("/monsters/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def monster_form(item_id=None):
    monster = db.get_or_404(Monster, item_id) if item_id else Monster()
    if request.method == "POST":
        monster.name = request.form["name"].strip()
        monster.experience = int(request.form.get("experience") or 0)
        monster.life = int(request.form.get("life") or 0)
        monster.image_url = request.form.get("image_url", "").strip()
        monster.weaknesses = _element_values("weakness")
        monster.attacks = _element_values("attack")
        db.session.add(monster)
        db.session.commit()
        flash("Monstro salvo com sucesso.", "success")
        return redirect(url_for("main.monsters_list"))
    return render_template("monsters/form.html", monster=monster)


@bp.post("/monsters/<int:item_id>/delete")
@admin_required
def monster_delete(item_id):
    monster = db.get_or_404(Monster, item_id)
    db.session.delete(monster)
    db.session.commit()
    flash("Monstro excluído.", "success")
    return redirect(url_for("main.monsters_list"))


@bp.route("/charms")
def charms_list():
    q = _search_term()
    stmt = db.select(Charm)
    if q:
        stmt = stmt.where(or_(Charm.name.ilike(f"%{q}%"), Charm.description.ilike(f"%{q}%"), Charm.category.ilike(f"%{q}%")))
    charms = db.session.scalars(stmt.order_by(Charm.category, Charm.name)).all()
    return render_template("charms/list.html", charms=charms, q=q)


@bp.route("/charms/new", methods=["GET", "POST"])
@bp.route("/charms/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def charm_form(item_id=None):
    charm = db.get_or_404(Charm, item_id) if item_id else Charm()
    if request.method == "POST":
        charm.name = request.form["name"].strip()
        charm.category = request.form["category"]
        charm.description = request.form["description"].strip()
        charm.image_url = request.form.get("image_url", "").strip()
        db.session.add(charm)
        db.session.commit()
        flash("Charm salvo com sucesso.", "success")
        return redirect(url_for("main.charms_list"))
    return render_template("charms/form.html", charm=charm)


@bp.post("/charms/<int:item_id>/delete")
@admin_required
def charm_delete(item_id):
    charm = db.get_or_404(Charm, item_id)
    db.session.delete(charm)
    db.session.commit()
    flash("Charm excluído.", "success")
    return redirect(url_for("main.charms_list"))


@bp.route("/hunts")
def hunts_list():
    q = _search_term()
    stmt = db.select(Hunt)
    if q:
        stmt = stmt.where(or_(Hunt.name.ilike(f"%{q}%"), Hunt.location.ilike(f"%{q}%")))
    hunts = db.session.scalars(stmt.order_by(Hunt.name)).all()
    return render_template("hunts/list.html", hunts=hunts, q=q)


@bp.route("/hunts/new", methods=["GET", "POST"])
@bp.route("/hunts/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def hunt_form(item_id=None):
    hunt = db.get_or_404(Hunt, item_id) if item_id else Hunt()
    monsters = db.session.scalars(db.select(Monster).order_by(Monster.name)).all()
    charms = db.session.scalars(db.select(Charm).order_by(Charm.category, Charm.name)).all()
    if request.method == "POST":
        hunt.name = request.form["name"].strip()
        hunt.location = request.form["location"].strip()
        hunt.protections = _element_values("protection", with_value=False)
        hunt.weaknesses = _element_values("hunt_weakness", with_value=False)
        monster_ids = [int(x) for x in request.form.getlist("monster_ids")]
        charm_ids = [int(x) for x in request.form.getlist("charm_ids")]
        hunt.monsters = db.session.scalars(db.select(Monster).where(Monster.id.in_(monster_ids))).all() if monster_ids else []
        hunt.charms = db.session.scalars(db.select(Charm).where(Charm.id.in_(charm_ids))).all() if charm_ids else []
        db.session.add(hunt)
        db.session.commit()
        flash("Hunt salva com sucesso.", "success")
        return redirect(url_for("main.hunts_list"))
    return render_template("hunts/form.html", hunt=hunt, monsters=monsters, charms=charms)


@bp.get("/hunts/<int:item_id>")
def hunt_view(item_id):
    hunt = db.get_or_404(Hunt, item_id)
    return render_template("hunts/view.html", hunt=hunt)


@bp.post("/hunts/<int:item_id>/delete")
@admin_required
def hunt_delete(item_id):
    hunt = db.get_or_404(Hunt, item_id)
    db.session.delete(hunt)
    db.session.commit()
    flash("Hunt excluída.", "success")
    return redirect(url_for("main.hunts_list"))


@bp.route("/imbuements")
def imbuements_list():
    q = _search_term()
    stmt = db.select(Imbuement)
    if q:
        stmt = stmt.where(or_(Imbuement.name.ilike(f"%{q}%"), Imbuement.level.ilike(f"%{q}%"), Imbuement.kind.ilike(f"%{q}%")))
    imbuements = db.session.scalars(stmt.order_by(Imbuement.name, Imbuement.level)).all()
    return render_template("imbuements/list.html", imbuements=imbuements, q=q)


@bp.route("/imbuements/new", methods=["GET", "POST"])
@bp.route("/imbuements/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def imbuement_form(item_id=None):
    imbuement = db.get_or_404(Imbuement, item_id) if item_id else Imbuement(level="Basic", kind="Ataque")
    if request.method == "POST":
        level = request.form["level"]
        expected = LEVEL_ITEM_COUNT[level]
        imbuement.name = request.form["name"].strip()
        imbuement.level = level
        imbuement.kind = request.form["kind"]
        imbuement.items.clear()
        for index in range(1, expected + 1):
            name = request.form.get(f"item_name_{index}", "").strip()
            if name:
                imbuement.items.append(ImbuementItem(
                    name=name,
                    quantity=int(request.form.get(f"item_quantity_{index}") or 1),
                    image_url=request.form.get(f"item_image_{index}", "").strip(),
                ))
        if len(imbuement.items) != expected:
            flash(f"O nível {level} exige exatamente {expected} item(ns).", "danger")
            return render_template("imbuements/form.html", imbuement=imbuement)
        db.session.add(imbuement)
        db.session.commit()
        flash("Imbuement salvo com sucesso.", "success")
        return redirect(url_for("main.imbuements_list"))
    return render_template("imbuements/form.html", imbuement=imbuement)


@bp.post("/imbuements/<int:item_id>/delete")
@admin_required
def imbuement_delete(item_id):
    imbuement = db.get_or_404(Imbuement, item_id)
    db.session.delete(imbuement)
    db.session.commit()
    flash("Imbuement excluído.", "success")
    return redirect(url_for("main.imbuements_list"))
