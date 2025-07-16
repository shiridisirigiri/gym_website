from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import razorpay
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Razorpay setup
razorpay_client = razorpay.Client(auth=("rzp_test_qM0wzz6NIH2B7q", "jvIdIUw6eyCChirrLwzBgHrt"))

# Database Models
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    membership = db.Column(db.String(50), nullable=False)
    payment_id = db.Column(db.String(100))
    photo_path = db.Column(db.String(255))  # New: Save image path
    joined_on = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/')
def index():
    return render_template("index.html", no_footer=True)

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        contact = Contact(name=name, email=email, message=message)
        db.session.add(contact)
        db.session.commit()
        return redirect('/thankyou')
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        membership = request.form.get('membership')
        amount_rupees = int(request.form.get('amount'))
        photo = request.files['photo']

        # Save photo
        photo_path = None
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(file_path)
            photo_path = file_path  # Save path in DB

        # Create Razorpay order
        amount_paise = amount_rupees * 100
        payment = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        return render_template('payment.html',
                               payment=payment,
                               name=name,
                               email=email,
                               phone=phone,
                               age=age,
                               gender=gender,
                               membership=membership,
                               amount=amount_rupees,
                               photo_path=photo_path)
    return render_template('register.html')

@app.route('/payment_success', methods=['POST'])
def payment_success():
    payment_id = request.form.get('razorpay_payment_id')
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    age = request.form.get('age')
    gender = request.form.get('gender')
    membership = request.form.get('membership')
    photo_path = request.form.get('photo_path')  # Hidden input from payment.html

    member = Member(
        name=name,
        email=email,
        phone=phone,
        age=age,
        gender=gender,
        membership=membership,
        payment_id=payment_id,
        photo_path=photo_path
    )
    db.session.add(member)
    db.session.commit()

    return redirect('/thankyou')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
