import os
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from helpers import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient("mongodb+srv://Fawaz:fawaz1111@garbage-detection.dvpjxvx.mongodb.net/")
db = client["Garbage_Detection_Project"]
users_collection = db["Users"]

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
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", message="Must provide username")
        
        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("login.html", message="Must provide password")
        
        # Query database for username
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})#              

        # Ensure username exists and password is correct

        if user is None or not check_password_hash(user["password"], password):
            return render_template("login.html", message="Invalid username or password")
        
        # Remember which user has logged in
        session["user_id"] = str(user["_id"])

        return redirect("/")
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    return redirect("/")

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
        if not request.form.get("confirm_password"):
            return render_template("register.html", message="Must provide password confirmation")
        
        # Ensure password and confirmation match
        if request.form.get("password") != request.form.get("confirm_password"):
            return render_template("register.html", message="Passwords do not match")
         
        # Check if username already exists(Fawaz)

        username = request.form.get("username")
        email_id = request.form.get("email")
        if users_collection.find_one({"username": username}):
            return render_template("register.html", message="Username already exists")

        # Hash the password
        hashed_password = generate_password_hash(request.form.get("password"))

        # Store the user in the database(Fawaz)
        users_collection.insert_one({
            "username": username,
            "email": email_id,
            "password": hashed_password
        })

        return render_template("login.html")

    else:
        return render_template("register.html")