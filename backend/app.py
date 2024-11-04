from flask import Flask,request,abort,jsonify,session
from models import User,db
from config import ApplicationConfig
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(ApplicationConfig)
server_session = Session(app)
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000/login"])

with app.app_context():
    db.create_all()


@app.route('/@me')
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "Error":"Unauthorized"
        }),401
    user = User.query.filter_by(id =user_id).first()
    return jsonify({
                "id":user.id,
                "name": user.name,
                "username": user.username,
                "email":user.email,
                "password":user.password_hash

        })


@app.route("/register", methods=['POST', 'GET'])
def register_user():
    if request.method == 'POST':
        # Validate request body to ensure all required fields are present
        required_fields = ['name', 'username', 'email', 'password_hash', 'confirm_password_hash']
        missing_fields = [field for field in required_fields if field not in request.json]

        if missing_fields:
            return jsonify({
                "Error": f"Missing fields: {', '.join(missing_fields)}"
            }), 400  # Bad Request
        
        name = request.json['name']
        username = request.json['username']
        email = request.json['email']
        password_hash = request.json['password_hash']
        confirm_password = request.json['confirm_password_hash']

        # Check if password and confirm password match
        if password_hash != confirm_password:
            return jsonify({
                "Error": "Passwords do not match"
            }), 400  # Bad Request
        
        # Check if username or email already exists
        user = User.query.filter_by(username=username).first()
        email_user = User.query.filter_by(email=email).first()

        parts = email.split('@')
        if parts[1] != "gmail.com":
            return jsonify({
                'Error':'Invalid email'
            }), 409
            
        if user:
            return jsonify({
                "Error": f"Username '{username}' already exists"
            }), 409  # Conflict

        if email_user:
            return jsonify({
                "Error": f"Email '{email}' is already registered"
            }), 409  # Conflict

        # Create new user if all checks pass
        try:
            new_user = User(name=name, username=username, email=email)
            new_user.set_password(password_hash)  # Set the password hash

            # Add and commit to the database
            db.session.add(new_user)
            db.session.commit()

            # Store the user ID in the session
            session['user_id'] = new_user.id

            return jsonify({
                "name": new_user.name,
                "username": new_user.username,
                "email": new_user.email
            }), 201  # Created
        
        except Exception as e:
            # Catch any database errors or unexpected exceptions
            db.session.rollback()  # Rollback in case of an error
            return jsonify({
                "Error": f"An error occurred during registration: {str(e)}"
            }), 500  # Internal Server Error
    
    # Handle GET request (optional)
    return jsonify({
        "Register": 'GET method called'
    }), 200


@app.route("/login", methods=['POST'])
def login():
    try:
        # Fetch username and password from the request
        username = request.json.get('username')
        password = request.json.get('password_hash')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Find user in the database
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            return jsonify({
                "name": user.name,
                "username": user.username,
                "email": user.email,
                "password": user.password_hash
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    
    except Exception as e:
        # In case of an unexpected error
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
