from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# DB-Config aus Environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Datenbankmodell
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=True)     # optionales Enddatum
    persons = db.Column(db.String(200), nullable=False)  # Name der Person

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Datenbank erstellen
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

# Register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "User exists"}), 400

    new_user = User(username=data["username"])
    new_user.set_password(data["password"])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "registered"})

# login
@app.route("/login", methods=["POST"])
def login_post():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]): 
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = user.id
    return jsonify({"status": "logged_in"})

#logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@app.route("/events")
def get_events():
    events = Event.query.all()
    return jsonify([{
        "id": e.id, 
        "title": e.title, 
        "start": e.start, 
        "end": e.end_date,
        "persons": e.persons.split(",")  # Array zurück
    } for e in events])


@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json()
    title = data.get('title')
    start = data.get('start')
    end_date = data.get('end_date')

    # Enddatum +1 Tag, weil FullCalendar exklusif end betrachtet
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        end_date = end_dt.strftime("%Y-%m-%d")


    persons = ",".join(data.get("persons", []))  # Array → String
    new_event = Event(title=title, start=start, end_date=end_date, persons=persons)
    db.session.add(new_event)
    db.session.commit()

    return jsonify({"status": "success"})

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({"status": "deleted"})

# Profile page
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    return render_template("profile.html", username=user.username)

@app.route("/cleaning")
def cleaning():
    return render_template("cleaning.html")

@app.route("/polls")
def polls():
    return render_template("polls.html")

@app.route("/todo")
def todo():
    return render_template("todo.html")

if __name__ == "__main__":
    app.run()