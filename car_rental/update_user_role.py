from app import app, db, User
from werkzeug.security import generate_password_hash
import sys

def update_user_role(email):
    with app.app_context():
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"User with email {email} not found")
            return False
        
        # Update role to admin
        user.role = 'admin'
        db.session.commit()
        
        print(f"User {user.fname} {user.lname} ({user.email}) has been updated to admin role")
        return True

def create_admin_user(fname, lname, email, password):
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists")
            return False
        
        # Create new admin user
        hashed_password = generate_password_hash(password)
        new_user = User(
            fname=fname,
            lname=lname,
            email=email,
            password=hashed_password,
            role='admin'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"Admin user {fname} {lname} ({email}) has been created successfully")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_user_role.py [update_role email] OR [create_admin fname lname email password]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "update_role" and len(sys.argv) == 3:
        email = sys.argv[2]
        update_user_role(email)
    elif action == "create_admin" and len(sys.argv) == 6:
        fname = sys.argv[2]
        lname = sys.argv[3]
        email = sys.argv[4]
        password = sys.argv[5]
        create_admin_user(fname, lname, email, password)
    else:
        print("Usage: python update_user_role.py [update_role email] OR [create_admin fname lname email password]") 