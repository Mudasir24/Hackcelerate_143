import os
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from helpers import login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    # Set the cache control headers to prevent caching
    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers['Pragma'] = "no-cache"
    return response

@app.route('/')
@login_required
def index():
    """Home page"""
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html", message="Must provide username") 
        
        # Ensure email was submitted
        if not request.form.get("email"):
            return render_template("register.html", message="Must provide email")
        
        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("register.html", message="Must provide password")
        
        # Ensure password confirmation was submitted
        if not request.form.get("confirmation"):
            return render_template("register.html", message="Must provide password confirmation")
        
        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", message="Passwords do not match")
         
        # Check if username already exists(Fawaz)

        hashed_password = generate_password_hash(request.form.get("password"))

        # Store the user in the database(Fawaz)

        return render_template("login.html")




    else:
        return render_template("register.html")
        
