import os
from flask import Flask, render_template, redirect, request, session, url_for, flash
import base64
from flask_session import Session
from helpers import login_required,officer_login_required, detect_trash, estimate_trash_level
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import gridfs
from datetime import datetime
import numpy as np
import cv2

client = MongoClient("mongodb+srv://Fawaz:fawaz1111@garbage-detection.dvpjxvx.mongodb.net/")
db = client["Garbage_Detection_Project"]
users_collection = db["Users"]
officers_collection = db["Officers"]
complaints_collection = db["Complaints"]
user_images_collection = db["Images"]
fs = gridfs.GridFS(db)

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

        user = users_collection.find_one({"username": username})            

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
    
@app.route("/complaint", methods=["GET", "POST"])
@login_required
def complaint():
    """Complaint page"""
    if request.method == "POST":
        # Ensure complaint was submitted
        if 'image' not in request.files:
            flash('No image part in the form')
            return render_template("complaint.html", message="No image part in the form")
    
        file = request.files['image']
    
        if file.filename == '':
            flash('No image selected for uploading')
            return render_template("complaint.html", message="No image selected for uploading")
    
        # Collect image data
        file_ext = os.path.splitext(file.filename)[-1].lower().replace('.', '')
        image_data = file.read()
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Ensure address was submitted
        if not request.form.get("auto_address") and not request.form.get("manual_address"):
            return render_template("complaint.html", message="Must provide address")
        
        # Garbage detection
        nparray = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparray, cv2.IMREAD_COLOR)

        if image is None:
            return render_template("complaint.html", message="Invalid image format")
        
        image = cv2.resize(image, (700,500))
        has_trash, results = detect_trash(image)

        if not has_trash:
            return render_template("complaint.html", message="No trash detected in the image")
        
        # Estimate trash level
        trash_level, image = estimate_trash_level(image, results)

       # Database related coding
        address = request.form.get("auto_address") or request.form.get("manual_address")
        try:
            latitude = float(request.form.get("latitude", 0))  # Default to 0 if missing
            longitude = float(request.form.get("longitude", 0))
        except ValueError:
            return render_template("complaint.html", message="Invalid latitude/longitude")
        
        description = request.form.get("description")
        if not description or description.strip() == "":
            description = "No description provided"

        # Split address
        try:
            area, city, pincode, country = [x.strip() for x in address.split(",")]
        except ValueError:
            return render_template("complaint.html", message="Address format should be: area, city, pincode")
        
        file_id = fs.put(image_data, filename=file.filename)

        # Saving to database
        user_image = {
            "file_id": file_id,
            "image_data": image_b64,
            "file_type": file_ext,
            "user_id": session["user_id"],
            "area": area,
            "city": city,
            "pincode": pincode,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.utcnow()
        }
        image_result = user_images_collection.insert_one(user_image)
        image_file_id = image_result.inserted_id

        last_complaint = complaints_collection.find_one(sort=[("complaint_id", -1)])
        complaint_id = 1 if not last_complaint else last_complaint["complaint_id"] + 1

        complaint_doc = {
            "complaint_id": complaint_id,
            "user_id": session["user_id"],
            "image_file_id": image_file_id,
            "timestamp": datetime.utcnow(),
            "status": "new",
            "assigned_officer_id": None,
            "cleanup_image_file_id": None,
            "description": description,
        }

        complaints_collection.insert_one(complaint_doc)


        flash('Complaint registered successfully')
        return redirect("/")
    else:
        return render_template("complaint.html")
    
@app.route("/faq")
@login_required
def faq():
    """FAQ page"""
    return render_template("faq.html")

@app.route("/about")
@login_required
def about():
    """About page"""
    return render_template("about.html")

@app.route("/officer-login", methods=["GET", "POST"])
def officer_login():
    """Officer login page"""
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("officer-username"):
            return render_template("officer-login.html", message="Must provide username")
        
        # Ensure password was submitted
        if not request.form.get("officer-password"):
            return render_template("officer-login.html", message="Must provide password")
        
        #Database
        # Query database for username
        username = request.form.get("officer-username")
        password = request.form.get("officer-password")

        officer = officers_collection.find_one({"username":username})
        
        if officer is None or not check_password_hash(officer["password"], password):
            return render_template("officer-login.html", message="Invalid username or password")
        
        
        session["officer_id"] =  str(officer["_id"])

        return redirect("/officer-dash")
    
    else:
        return render_template("officer-login.html")
    
@app.route("/officer-dash")
@officer_login_required
def officer_dash():
    """Officer dashboard page"""
    return render_template("officer-dash.html")

@app.route("/complete", methods=["GET", "POST"])
@officer_login_required
def complete():
    """Complete complaint"""
    if request.method == "POST":
        
        render_template("complete.html")

    else:
        return render_template("complete.html")

    

    

