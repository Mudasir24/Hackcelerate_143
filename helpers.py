from functools import wraps
from flask import session, redirect,render_template


def login_required(f):
    """
    Decorator to check if the user is logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    
    return decorated_function