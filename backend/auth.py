"""Authentication routes: email/password accounts plus Google OAuth.

Sessions are tracked with Flask's signed-cookie session (see app.secret_key
in main.py) -- there is no server-side session table, the cookie itself
holds the user id and is tamper-proof as long as the secret key is kept
secret.

Required environment variables for Google sign-in to actually work:
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET  -- from the Google Cloud console,
    with an OAuth redirect URI of  http://localhost:8001/auth/google/callback
  FRONTEND_URL -- where to send the browser back to after a successful
    Google sign-in (defaults to http://localhost:5174)

Apple sign-in is not implemented: it requires a paid Apple Developer
account and an HTTPS redirect URI, so /apple/login is left as a stub that
reports the feature is unavailable.
"""

import os

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import create_user, find_or_create_google_user, find_user_by_email, find_user_by_id

oauth = OAuth()

auth_bp = Blueprint("auth", __name__)


def register_google_oauth():
    """Register the Google OAuth client with Authlib.

    Safe to call even when GOOGLE_CLIENT_ID/SECRET are unset: the client is
    simply registered with empty credentials, and requests to
    /auth/google/login will fail with a clear error from Google rather than
    crashing the app at startup.
    """
    oauth.register(
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def _user_to_dict(user):
    """Shape a `users` table row into the JSON representation sent to the frontend."""
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new email/password account and log the user in immediately."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if find_user_by_email(email) is not None:
        return jsonify({"error": "An account with that email already exists."}), 409

    user = create_user(email, generate_password_hash(password), name or None)
    session["user_id"] = user["id"]
    return jsonify({"user": _user_to_dict(user)})


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log an existing email/password account in."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = find_user_by_email(email)
    if user is None or user["password_hash"] is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    return jsonify({"user": _user_to_dict(user)})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear the current session."""
    session.clear()
    return jsonify({})


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return the currently logged-in user, or null if there isn't one.

    Always responds 200 (even when logged out) so the frontend can call
    this unconditionally on page load without special-casing errors.
    """
    user_id = session.get("user_id")
    user = find_user_by_id(user_id) if user_id is not None else None
    if user is None:
        session.clear()
        return jsonify({"user": None})
    return jsonify({"user": _user_to_dict(user)})


@auth_bp.route("/google/login", methods=["GET"])
def google_login():
    """Kick off the Google OAuth flow by redirecting to Google's consent screen."""
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    """Handle Google's redirect back after the user grants (or denies) consent."""
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") or {}
    user = find_or_create_google_user(
        sub=userinfo["sub"], email=userinfo["email"], name=userinfo.get("name")
    )
    session["user_id"] = user["id"]
    return redirect(os.environ.get("FRONTEND_URL", "http://localhost:5174"))


@auth_bp.route("/apple/login", methods=["GET"])
def apple_login():
    """Stub: Apple sign-in is not wired up (see module docstring for why)."""
    return jsonify({"error": "Apple sign-in is not configured yet."}), 501
