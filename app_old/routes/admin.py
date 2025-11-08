from __future__ import annotations

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from ..models import Admin, Member
from ..utils.auth import admin_login_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/")
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_login.html")


@admin_bp.post("/login")
def authenticate():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password_hash, password):
        session["admin_id"] = admin.id
        session.permanent = True
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("admin.login"))


@admin_bp.get("/dashboard")
@admin_login_required
def dashboard():
    members_count = Member.query.count()
    latest_members = (
        Member.query.order_by(Member.created_at.desc()).limit(5).all()
    )
    return render_template(
        "admin_dashboard.html",
        members_count=members_count,
        latest_members=latest_members,
    )


@admin_bp.post("/logout")
@admin_login_required
def logout():
    session.pop("admin_id", None)
    return redirect(url_for("public.index"))
