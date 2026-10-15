import os
import json
import hashlib

USERS_FILE = "users_db.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users_data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    email = email.strip().lower()
    users = load_users()
    
    if not email or not password:
        return False, "Email aur password khali nahi ho sakte!"
    if "@" not in email or "." not in email:
        return False, "Kripya ek valid Email address daalein!"
    if len(password) < 6:
        return False, "Password kam se kam 6 characters ka hona chahiye!"
    if email in users:
        return False, "Yeh email pehle se registered hai! Kripya Login karein."
        
    users[email] = hash_password(password)
    save_users(users)
    return True, "Registration successful! Ab aap login kar sakte hain."

def verify_user(email, password):
    email = email.strip().lower()
    users = load_users()
    
    if email in users and users[email] == hash_password(password):
        return True, "Login successful!"
    return False, "Galat Email ya Password! Dobara check karein."