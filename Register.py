from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from database import db 
import datetime

app = Flask(__name__)


CORS(app, resources={r"/api/*": {"origins": "*"}})
bcrypt = Bcrypt(app)
users_collection = db["users"]


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if users_collection.find_one({"email": data['email']}):
        return jsonify({"error": "Email already exists"}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = {
        "name": data['name'],
        "email": data['email'],
        "password": hashed_password,
        "role": data.get('role', 'jobseeker'),
        "created_at": datetime.datetime.utcnow()
    }
    users_collection.insert_one(new_user)
    return jsonify({"message": "Account created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = users_collection.find_one({"email": data['email']})

    if user:
        if user.get('role') != data.get('role'):
            return jsonify({"error": f"Account exists, but not as a {data.get('role')}"}), 401
            
        if bcrypt.check_password_hash(user['password'], data['password']):
            return jsonify({
                "message": "Login successful",
                "user": {"name": user['name'], "email": user['email'], "role": user['role']}
            }), 200
        else:
            return jsonify({"error": "Invalid password"}), 401
    return jsonify({"error": "Email not found"}), 404


@app.route('/api/user/change-password', methods=['PUT'])
def change_password():
    data = request.json
    email = data.get('email')
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found. Please log in again."}), 404

    if not bcrypt.check_password_hash(user['password'], current_password):
        return jsonify({"error": "Incorrect current password."}), 401

    hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_new_password}}
    )
    return jsonify({"message": "Password updated successfully"}), 200

@app.route('/api/user/delete-account', methods=['DELETE'])
def delete_account():
    data = request.json
    email = data.get('email')
    password = data.get('password') 

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "Account not found."}), 404

    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"error": "Incorrect password. Deletion cancelled."}), 401

    # Delete the user from the database
    result = users_collection.delete_one({"email": email})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Account permanently deleted."}), 200
    else:
        return jsonify({"error": "Failed to delete account from database."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
