from __future__ import annotations

from functools import wraps

from flask import jsonify, redirect, request, session, url_for


def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            if request.accept_mimetypes.accept_json:
                return jsonify({"error": "Authentification requise"}), 401
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped
