from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import secrets

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///car_rental.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')  # Only 'admin' or 'customer'
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    contact_add = db.Column(db.String(200))
    rentals = db.relationship('Rental', backref='customer', lazy=True)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer)
    car_type = db.Column(db.String(50))
    image = db.Column(db.String(100), default='default_car.jpg')
    daily_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='available')
    rentals = db.relationship('Rental', backref='car', lazy=True)
    maintenance = db.relationship('Maintenance', backref='car', lazy=True)

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    date_rent = db.Column(db.Date, nullable=False)
    date_return = db.Column(db.Date, nullable=False)
    time_depart = db.Column(db.String(10))
    time_arrive = db.Column(db.String(10))
    destination = db.Column(db.String(100))
    payment = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    transactions = db.relationship('Transaction', backref='rental', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    trans_name = db.Column(db.String(100))
    trans_detail = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    date = db.Column(db.Date, default=datetime.now().date())
    status = db.Column(db.String(20), default='pending')

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    issue = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    date = db.Column(db.Date, default=datetime.now().date())
    details = db.Column(db.Text)

class CustomerReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rental.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='pending')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

# Create all database tables and add default admin if it doesn't exist
with app.app_context():
    db.create_all()
    
    # Check if admin user exists, if not create one
    admin_exists = User.query.filter_by(email='admin@gmail.com').first()
    if not admin_exists:
        admin_user = User(
            fname='Admin',
            lname='User',
            email='admin@gmail.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created. Email: admin@gmail.com, Password: admin123")

# Utility functions
def is_admin():
    return 'role' in session and session['role'] == 'admin'

# ------------------------- ADMIN ROUTES -------------------------

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin middleware
@admin_bp.before_request
def require_admin():
    print(f"Admin middleware check: user_id={session.get('user_id')}, role={session.get('role')}")
    if 'user_id' not in session:
        print("Admin access denied: No user_id in session")
        abort(403)  # Forbidden
    if session.get('role') != 'admin':
        print(f"Admin access denied: Role '{session.get('role')}' is not admin")
        abort(403)  # Forbidden
    print("Admin access granted")

@admin_bp.route('/')
def dashboard():
    vehicles_count = Car.query.count()
    available_vehicles = Car.query.filter_by(status='available').count()
    booked_vehicles = Car.query.filter_by(status='booked').count()
    maintenance_vehicles = Car.query.filter_by(status='maintenance').count()
    
    # Get recent bookings
    recent_bookings = Rental.query.order_by(Rental.id.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                        vehicles_count=vehicles_count,
                        available_vehicles=available_vehicles,
                        booked_vehicles=booked_vehicles,
                        maintenance_vehicles=maintenance_vehicles,
                        recent_bookings=recent_bookings)

# Vehicle Management
@admin_bp.route('/vehicles')
def vehicles():
    cars = Car.query.all()
    return render_template('admin/vehicles.html', cars=cars)

@admin_bp.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        name = request.form.get('name')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        car_type = request.form.get('car_type')
        daily_price = request.form.get('daily_price')
        status = request.form.get('status', 'available')
        
        # Handle image upload if provided
        image = 'default_car.jpg'  # Default image
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.static_folder, 'images', filename)
                file.save(file_path)
                image = filename
        
        new_car = Car(
            name=name,
            brand=brand,
            model=model,
            year=year,
            car_type=car_type,
            daily_price=daily_price,
            status=status,
            image=image
        )
        
        db.session.add(new_car)
        db.session.commit()
        
        flash('Vehicle added successfully', 'success')
        return redirect(url_for('admin.vehicles'))
    
    return render_template('admin/add_vehicle.html')

@admin_bp.route('/vehicles/edit/<int:car_id>', methods=['GET', 'POST'])
def edit_vehicle(car_id):
    car = Car.query.get_or_404(car_id)
    
    if request.method == 'POST':
        car.name = request.form.get('name')
        car.brand = request.form.get('brand')
        car.model = request.form.get('model')
        car.year = request.form.get('year')
        car.car_type = request.form.get('car_type')
        car.daily_price = request.form.get('daily_price')
        car.status = request.form.get('status')
        
        # Handle image upload if provided
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.static_folder, 'images', filename)
                file.save(file_path)
                car.image = filename
        
        db.session.commit()
        flash('Vehicle updated successfully', 'success')
        return redirect(url_for('admin.vehicles'))
    
    return render_template('admin/edit_vehicle.html', car=car)

@admin_bp.route('/vehicles/delete/<int:car_id>')
def delete_vehicle(car_id):
    car = Car.query.get_or_404(car_id)
    
    # Check if car is currently in use
    active_rentals = Rental.query.filter_by(car_id=car_id).filter(Rental.status.in_(['confirmed', 'active'])).first()
    
    if active_rentals:
        flash('Cannot delete vehicle with active rentals', 'danger')
        return redirect(url_for('admin.vehicles'))
    
    db.session.delete(car)
    db.session.commit()
    
    flash('Vehicle deleted successfully', 'success')
    return redirect(url_for('admin.vehicles'))

# Maintenance Management
@admin_bp.route('/maintenance')
def maintenance():
    maintenance_records = Maintenance.query.all()
    return render_template('admin/maintenance.html', maintenance_records=maintenance_records)

@admin_bp.route('/maintenance/add', methods=['GET', 'POST'])
def add_maintenance():
    if request.method == 'POST':
        car_id = request.form.get('car_id')
        issue = request.form.get('issue')
        date_str = request.form.get('date')
        status = request.form.get('status')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            new_maintenance = Maintenance(
                car_id=car_id,
                issue=issue,
                date=date,
                status=status
            )
            
            # Update car status if putting into maintenance
            car = Car.query.get(car_id)
            if status == 'Under Maintenance':
                car.status = 'maintenance'
            
            db.session.add(new_maintenance)
            db.session.commit()
            
            flash('Maintenance record added successfully', 'success')
            return redirect(url_for('admin.maintenance'))
            
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD format.', 'danger')
            cars = Car.query.all()
            return render_template('admin/add_maintenance.html', cars=cars)
    
    cars = Car.query.all()
    return render_template('admin/add_maintenance.html', cars=cars)

# Bookings View
@admin_bp.route('/bookings')
def bookings():
    rentals = Rental.query.all()
    return render_template('admin/bookings.html', rentals=rentals)

@admin_bp.route('/bookings/view/<int:rental_id>')
def view_booking(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    transactions = Transaction.query.filter_by(rental_id=rental_id).all()
    
    return render_template('admin/booking_details.html', rental=rental, transactions=transactions)

@admin_bp.route('/bookings/update-status/<int:rental_id>', methods=['POST'])
def update_booking_status(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    new_status = request.form.get('status')
    
    rental.status = new_status
    
    # Update car status based on rental status
    car = Car.query.get(rental.car_id)
    
    if new_status == 'confirmed':
        car.status = 'booked'
    elif new_status == 'active':
        car.status = 'rented'
    elif new_status in ['completed', 'canceled']:
        car.status = 'available'
    
    db.session.commit()
    flash('Booking status updated successfully', 'success')
    return redirect(url_for('admin.view_booking', rental_id=rental_id))

@admin_bp.route('/users')
def users():
    users = User.query.filter_by(role='customer').all()  # Only show customers
    return render_template('admin/users.html', users=users)

@admin_bp.route('/reports')
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/rentals', methods=['GET', 'POST'])
def rental_reports():
    rentals = []
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        rentals = Rental.query.filter(Rental.date_rent >= start_date, Rental.date_rent <= end_date).all()
    return render_template('admin/rental_reports.html', rentals=rentals)

@admin_bp.route('/reports/transactions', methods=['GET', 'POST'])
def transaction_reports():
    transactions = []
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        transactions = Transaction.query.filter(Transaction.date >= start_date, Transaction.date <= end_date).all()
    return render_template('admin/transaction_reports.html', transactions=transactions)

# Register the admin blueprint
app.register_blueprint(admin_bp)

# ------------------------- USER ROUTES -------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            print(f"User logged in: {email}, Role: {user.role}")
            
            if user.role == 'admin':
                return redirect('/admin')
            return redirect(url_for('dashboard'))
        else:
            if user:
                print(f"Failed login attempt: {email} - Password incorrect")
            else:
                print(f"Failed login attempt: {email} - User not found")
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Check if email already exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            fname=fname,
            lname=lname,
            email=email,
            phone=phone,
            password=hashed_password,
            role='customer'  # Always set as customer
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    active_rentals = Rental.query.filter_by(user_id=user.id, status='active').all()
    upcoming_rentals = Rental.query.filter_by(user_id=user.id, status='confirmed').all()
    
    return render_template('dashboard.html', user=user, active_rentals=active_rentals, upcoming_rentals=upcoming_rentals)

@app.route('/cars')
def cars():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get all cars with status 'available'
    cars = Car.query.filter_by(status='available').all()
    return render_template('car_listing.html', cars=cars)

@app.route('/car/<int:car_id>')
def car_details(car_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car)

@app.route('/debug_session')
def debug_session():
    session_info = {
        'user_id': session.get('user_id', 'Not set'),
        'role': session.get('role', 'Not set'),
        'is_admin': is_admin()
    }
    
    return render_template('debug_session.html', session_info=session_info)

@app.route('/debug_login')
def debug_login():
    # This route will force-set the admin role for debugging
    user = User.query.filter_by(email='admin@gmail.com').first()
    if user:
        session['user_id'] = user.id
        session['role'] = 'admin'
        print(f"Debug login activated: user_id={user.id}, role=admin")
        flash('Admin login successful via debug route', 'success')
        return redirect('/admin')
    else:
        flash('Admin user not found', 'danger')
        return redirect(url_for('login'))

# Add all the remaining routes from above
@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book_car(car_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    car = Car.query.get_or_404(car_id)
    
    # Prevent booking if car is not available
    if car.status != 'available':
        flash('This car is not available for booking.', 'danger')
        return redirect(url_for('cars'))
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        time_depart = request.form.get('time_depart')
        destination = request.form.get('destination')
        
        # Calculate number of days
        delta = end_date - start_date
        days = delta.days + 1
        
        # Calculate total price
        total_price = days * car.daily_price
        
        new_rental = Rental(
            user_id=session['user_id'],
            car_id=car_id,
            date_rent=start_date,
            date_return=end_date,
            time_depart=time_depart,
            destination=destination,
            payment=total_price,
            status='pending'
        )
        
        db.session.add(new_rental)
        db.session.commit()
        
        return redirect(url_for('booking_confirmation', rental_id=new_rental.id))
    
    return render_template('booking.html', car=car)

@app.route('/booking-confirmation/<int:rental_id>')
def booking_confirmation(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    rental = Rental.query.get_or_404(rental_id)
    
    # Security check
    if rental.user_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('booking_confirmation.html', rental=rental)

@app.route('/payment/<int:rental_id>', methods=['GET', 'POST'])
def payment(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    rental = Rental.query.get_or_404(rental_id)
    
    # Security check
    if rental.user_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # Create a transaction
        new_transaction = Transaction(
            rental_id=rental.id,
            amount=rental.payment,
            payment_method=payment_method,
            status='paid',
            trans_name=f"Payment for rental #{rental.id}"
        )
        
        # Update rental status
        rental.status = 'confirmed'
        
        # Update car status
        car = Car.query.get(rental.car_id)
        car.status = 'booked'
        
        db.session.add(new_transaction)
        db.session.commit()
        
        flash('Payment successful! Your booking is confirmed.', 'success')
        return redirect(url_for('my_rentals'))
    
    return render_template('payment.html', rental=rental)

@app.route('/my-rentals')
def my_rentals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    active_rentals = Rental.query.filter_by(user_id=session['user_id']).filter(Rental.status.in_(['confirmed', 'active'])).all()
    past_rentals = Rental.query.filter_by(user_id=session['user_id']).filter(Rental.status.in_(['completed', 'canceled'])).all()
    
    return render_template('my_rentals.html', active_rentals=active_rentals, past_rentals=past_rentals)

@app.route('/cancel-booking/<int:rental_id>')
def cancel_booking(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    rental = Rental.query.get_or_404(rental_id)
    
    # Security check
    if rental.user_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Only allow cancellation of pending or confirmed bookings
    if rental.status in ['pending', 'confirmed']:
        rental.status = 'canceled'
        
        # If confirmed, then free up the car
        if rental.status == 'confirmed':
            car = Car.query.get(rental.car_id)
            car.status = 'available'
        
        db.session.commit()
        flash('Booking canceled successfully', 'success')
    else:
        flash('Cannot cancel this booking at its current state', 'danger')
    
    return redirect(url_for('my_rentals'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    user.fname = request.form.get('fname')
    user.lname = request.form.get('lname')
    user.phone = request.form.get('phone')
    user.contact_add = request.form.get('contact_add')
    
    # Update password if provided
    new_password = request.form.get('new_password')
    if new_password:
        user.password = generate_password_hash(new_password)
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.context_processor
def utility_processor():
    current_year = datetime.now().year
    now = datetime.now()
    return dict(current_year=current_year, now=now)

@app.context_processor
def admin_utility_processor():
    return dict(is_admin=is_admin)

if __name__ == '__main__':
    app.run(debug=True) 