from flask import Flask, render_template, request, redirect
import sqlite3
import razorpay
import os

app = Flask(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=("rzp_test_qM0wzz6NIH2B7q", "jvIdIUw6eyCChirrLwzBgHrt"))

def init_db():
    try:
        db_path = os.path.join(os.getcwd(), 'gym.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                membership TEXT NOT NULL,
                payment_id TEXT,
                joined_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] DB Init Failed: {e}")

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

        conn = sqlite3.connect('gym.db')
        c = conn.cursor()
        c.execute('INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)', (name, email, message))
        conn.commit()
        conn.close()

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
        amount_paise = amount_rupees * 100  # Razorpay uses paise

        # Create Razorpay order
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
                               amount=amount_rupees)

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

    conn = sqlite3.connect('gym.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO members (name, email, phone, age, gender, membership, payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, age, gender, membership, payment_id))
    conn.commit()
    conn.close()

    return redirect('/thankyou')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))  # Use PORT from env or default 5000
    app.run(host="0.0.0.0", port=port)
