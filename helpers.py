import os

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(p):
    """Check if the user has logged in"""
    @wraps(p)
    def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return redirect("/login")
            return p(*args, **kwargs)
    return decorated_function

def error(err):
    """Templates out errors"""
    return render_template("error.html", error=err)

def validate():
     """Validate the form"""
     username = request.form.get("username")
     password = request.form.get("password")

     if not username:
          return None, None, "You forgot your name?!"

     if not password:
          return None, None, "You forgot your password."

     return username, password, None
