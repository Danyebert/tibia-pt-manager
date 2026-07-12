from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_
from datetime import datetime
from models import Charm, Hunt, HuntMonsterCharm, Imbuement, ImbuementItem, Monster, User, db
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
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(db.select(User).where(User.username == username))
        if user and user.is_admin and check_password_hash(user.password_hash, password):
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            session.clear()
            session["user_id"] = user.id
            session["is_admin"] = True
            session["admin_username"] = user.username
            session["admin_name"] = user.name
            flash("Login realizado com sucesso.", "success")
            next_url = request.args.get("next")
            return redirect(next_url if next_url and next_url.startswith("/") else url_for("main.admin_panel"))
        flash("Usuário ou senha inválidos, ou usuário inativo.", "danger")
    return render_template("admin/login.html")


@bp.get("/admin")
@admin_required
def admin_panel():
    stats = {
        "monsters": db.session.scalar(db.select(func.count()).select_from(Monster)),
        "charms": db.session.scalar(db.select(func.count()).select_from(Charm)),
        "hunts": db.session.scalar(db.select(func.count()).select_from(Hunt)),
        "imbuements": db.session.scalar(db.select(func.count()).select_from(Imbuement)),
        "users": db.session.scalar(db.select(func.count()).select_from(User)),
    }
    return render_template("admin/panel.html", stats=stats)


@bp.post("/admin/logout")
def admin_logout():
    session.clear()
    flash("Você saiu da área administrativa.", "success")
    return redirect(url_for("main.dashboard"))


@bp.get("/admin/users")
@admin_required
def users_list():
    users = db.session.scalars(db.select(User).order_by(User.name, User.username)).all()
    return render_template("admin/users/list.html", users=users)


@bp.route("/admin/users/new", methods=["GET", "POST"])
@bp.route("/admin/users/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def user_form(item_id=None):
    user = db.get_or_404(User, item_id) if item_id else User(role="admin", active=True)
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        existing = db.session.scalar(db.select(User).where(User.username == username, User.id != (user.id or 0)))
        if existing:
            flash("Este nome de usuário já está cadastrado.", "danger")
            return render_template("admin/users/form.html", user=user)
        user.name = request.form.get("name", "").strip()
        user.username = username
        user.role = "admin"
        user.active = request.form.get("active") == "on"
        if not user.id and not password:
            flash("Informe uma senha para o novo administrador.", "danger")
            return render_template("admin/users/form.html", user=user)
        if password:
            user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        flash("Administrador salvo com sucesso.", "success")
        return redirect(url_for("main.users_list"))
    return render_template("admin/users/form.html", user=user)


@bp.post("/admin/users/<int:item_id>/delete")
@admin_required
def user_delete(item_id):
    user = db.get_or_404(User, item_id)
    if user.id == session.get("user_id"):
        flash("Você não pode excluir o usuário que está usando no momento.", "warning")
        return redirect(url_for("main.users_list"))
    active_admins = db.session.scalar(db.select(func.count()).select_from(User).where(User.role == "admin", User.active.is_(True)))
    if user.active and active_admins <= 1:
        flash("Não é possível excluir o último administrador ativo.", "warning")
        return redirect(url_for("main.users_list"))
    db.session.delete(user)
    db.session.commit()
    flash("Administrador excluído.", "success")
    return redirect(url_for("main.users_list"))


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
    major_charms = db.session.scalars(
        db.select(Charm).where(Charm.category == "Major").order_by(Charm.name)
    ).all()
    minor_charms = db.session.scalars(
        db.select(Charm).where(Charm.category == "Minor").order_by(Charm.name)
    ).all()

    if request.method == "POST":
        hunt.name = request.form["name"].strip()
        hunt.location = request.form["location"].strip()
        hunt.protections = _element_values("protection", with_value=False)
        hunt.weaknesses = _element_values("hunt_weakness", with_value=False)

        monster_ids = [int(x) for x in request.form.getlist("monster_ids")]
        selected_monsters = (
            db.session.scalars(db.select(Monster).where(Monster.id.in_(monster_ids))).all()
            if monster_ids else []
        )
        hunt.monsters = selected_monsters
        db.session.add(hunt)
        db.session.flush()

        assignments_by_monster = {
            assignment.monster_id: assignment
            for assignment in hunt.monster_charm_assignments
        }

        for monster_id in monster_ids:
            assignment = assignments_by_monster.get(monster_id)
            if assignment is None:
                assignment = HuntMonsterCharm(hunt_id=hunt.id, monster_id=monster_id)
                db.session.add(assignment)

            major_id = request.form.get(f"major_charm_{monster_id}", "").strip()
            minor_id = request.form.get(f"minor_charm_{monster_id}", "").strip()
            priority_raw = request.form.get(f"charm_priority_{monster_id}", "3").strip()

            assignment.major_charm_id = int(major_id) if major_id else None
            assignment.minor_charm_id = int(minor_id) if minor_id else None
            try:
                assignment.priority = max(1, min(5, int(priority_raw)))
            except ValueError:
                assignment.priority = 3

        for monster_id, assignment in assignments_by_monster.items():
            if monster_id not in monster_ids:
                db.session.delete(assignment)

        db.session.commit()
        flash("Hunt salva com sucesso.", "success")
        return redirect(url_for("main.hunt_view", item_id=hunt.id))

    assignments = {
        assignment.monster_id: assignment
        for assignment in hunt.monster_charm_assignments
    }
    return render_template(
        "hunts/form.html",
        hunt=hunt,
        monsters=monsters,
        major_charms=major_charms,
        minor_charms=minor_charms,
        assignments=assignments,
    )


@bp.get("/hunts/<int:item_id>")
def hunt_view(item_id):
    hunt = db.get_or_404(Hunt, item_id)
    assignments = {
        assignment.monster_id: assignment
        for assignment in hunt.monster_charm_assignments
    }

    # Soma os danos de cada elemento entre todos os monstros da hunt.
    # Exemplo: Energy 500 + Energy 700 + Energy 300 = Energy 1500.
    # O cálculo considera todos os tipos de ataque cadastrados, inclusive Physical.
    damage_by_element = {}

    for monster in hunt.monsters:
        for attack in (monster.attacks or []):
            element = attack.get("element")
            if not element:
                continue
            try:
                damage = int(attack.get("value") or 0)
            except (TypeError, ValueError):
                damage = 0
            damage_by_element[element] = damage_by_element.get(element, 0) + damage

    protection_ranking = sorted(
        (
            {"element": element, "damage": damage}
            for element, damage in damage_by_element.items()
        ),
        key=lambda item: (-item["damage"], item["element"]),
    )

    return render_template(
        "hunts/view.html",
        hunt=hunt,
        assignments=assignments,
        protection_ranking=protection_ranking,
    )


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
