from functools import wraps
from flask import flash, redirect, request, session, url_for


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Entre como administrador para acessar essa área.", "warning")
            return redirect(url_for("main.admin_login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped
