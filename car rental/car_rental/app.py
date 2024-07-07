from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
import bcrypt
from pymongo import MongoClient
from config import SECRET_KEY
from random import randint

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient('mongodb://localhost:27017/')
db = client['mydb']  
users_collection = db['login']  
bookings_collection = db['bookings']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        email = request.form['email']

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        users_collection.insert_one({'username': username, 'password': hashed_password, 'email': email, 'bookings': []})

        return redirect(url_for('booking'))  
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        user = users_collection.find_one({'email': email})

        if user and bcrypt.checkpw(password, user['password']):
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('booking'))

        error = 'Invalid email or password. Please try again.'
        return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')
  
@app.route('/add_car_to_db', methods=['POST'])
def add_car_to_db():
    data = request.json
    car_name = data['carName']
    rent_per_day = data['rentPerDay']
    pickup_date = data['pickupDate']
    return_date = data['returnDate']
    email = session.get('email')
    booking_id = str(randint(1000, 9999))
    booking_data = {
        '_id': booking_id,
        'car_name': car_name,
        'rent_per_day': rent_per_day,
        'pickup_date': pickup_date,
        'return_date': return_date,
        'email': email
    }
    bookings_collection.insert_one(booking_data)

    users_collection.update_one({'email': email}, {'$push': {'bookings': booking_data}})
    
    return {'success': True, 'message': 'Data stored successfully', 'booking_id': booking_id}

@app.route('/compact')
def compact():
    return render_template('compact.html')

@app.route('/economy')
def economy():
    return render_template('economy.html')

@app.route('/fullsize')
def fullsize():
    return render_template('fullsize.html')

@app.route('/luxury')
def luxury():
    return render_template('luxury.html')



@app.route('/suv')
def suv():
    return render_template('suv.html')

@app.route('/terms')
def terms():
    booking_id = request.args.get('booking_id')  
    return render_template('terms.html', booking_id=booking_id)

@app.route('/invoice/<booking_id>')
def invoice(booking_id):
    booking = bookings_collection.find_one({'_id': booking_id})

    if booking:
        return render_template('invoice.html', booking=booking)
    else:
        return "No booking found with this ID."

@app.route('/cancel_booking', methods=['GET', 'POST'])
def cancel_booking():
    if request.method == 'POST':
        booking_id = request.form['booking_id']
        booking = bookings_collection.find_one({'_id': booking_id})

        if booking:
            bookings_collection.delete_one({'_id': booking_id})
            message = "Booking canceled successfully."
        else:
            message = "No booking found with this ID."

        return render_template('cancel_booking.html', message=message)
    
    return render_template('cancel_booking.html')

@app.route('/update_booking', methods=['GET', 'POST'])
def update_booking():
    if request.method == 'POST':
        booking_id = request.form['booking_id']

        booking = bookings_collection.find_one({'_id': booking_id})

        if booking:
            return render_template('update_booking_form.html', booking=booking)
        else:
            message = "No booking found with this ID."
            return render_template('update_booking.html', message=message)
    
    return render_template('update_booking.html')

@app.route('/update_booking_form/<booking_id>', methods=['POST'])
def update_booking_form(booking_id):
    booking = bookings_collection.find_one({'_id': booking_id})

    if not booking:
        return "No booking found with this ID."

    pickup_date = request.form['pickup_date']
    return_date = request.form['return_date']

    updated_booking = {
        'pickup_date': pickup_date,
        'return_date': return_date,
    }

    bookings_collection.update_one({'_id': booking_id}, {'$set': updated_booking})
    message = "Booking updated successfully."
    return render_template('update_booking_form.html', booking=updated_booking, message=message)

@app.route('/profile')
def profile():
    if 'email' in session:
        email = session['email']
        user = users_collection.find_one({'email': email})
        if user:
            bookings = user.get('bookings', [])
            return render_template('profile.html', email=email, bookings=bookings)
    return redirect(url_for('register'))

@app.route('/logout')
def logout():
    session.clear() 
    user_id = session.get('user_id')
    if user_id:
        user_data = db.users.find_one_and_delete({'_id': user_id})
        if user_data:
            return redirect(url_for('index'))
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)
