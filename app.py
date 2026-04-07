import os
import sqlite3
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)

# ─── Database Configuration ─────────────────────────────────────────
DATABASE = 'datapenjualan.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Inisialisasi DB jika belum ada
def init_db():
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS penjualan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                date TEXT NOT NULL,
                purchase_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'Success',
                note TEXT
            )
        ''')
        # Cek apakah tabel kosong, jika iya masukkan data awal
        cur.execute("SELECT COUNT(*) FROM penjualan")
        if cur.fetchone()[0] == 0:
            dummy_data = [
                ('Sigit Ramadhan', '2025-01-12', 2400000.00, 'Success', ''),
                ('Dwi Santoso', '2025-01-14', 850000.00, 'Failed', 'Card declined'),
                ('Andi Pratama', '2025-01-16', 3100000.00, 'Success', ''),
                ('Rahma Hapsari', '2025-01-18', 560000.00, 'Success', ''),
                ('Bagas Nugroho', '2025-01-19', 1750000.00, 'Failed', ''),
                ('Citra Dewi', '2024-12-05', 2200000.00, 'Success', ''),
                ('Fajar Kusuma', '2024-12-12', 1800000.00, 'Success', ''),
                ('Nadia Putri', '2024-12-22', 1200000.00, 'Success', '')
            ]
            cur.executemany("INSERT INTO penjualan (customer_name, date, purchase_amount, payment_status, note) VALUES (?, ?, ?, ?, ?)", dummy_data)
            db.commit()

# Ensure db is initialized at startup
with app.app_context():
    init_db()


# ─── Jinja Filter ────────────────────────────────────────────────────
def format_number(value):
    """Format number with dots as thousand separator (Indonesian style)."""
    if isinstance(value, (int, float)):
        return '{:,.0f}'.format(value).replace(',', '.')
    return value

app.jinja_env.filters['format_number'] = format_number


# ─── Page Routes ─────────────────────────────────────────────────────
@app.route('/')
def index():
    cur = get_db().cursor()

    cur.execute("SELECT COUNT(DISTINCT customer_name) FROM penjualan")
    jumlahcust = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(purchase_amount), 0) FROM penjualan WHERE payment_status != 'failed'")
    total = cur.fetchone()[0]
    formatted_total = format_number(total)

    cur.execute("SELECT id, customer_name, purchase_amount, payment_status, date FROM penjualan ORDER BY date DESC LIMIT 5")
    data = cur.fetchall()
    
    return render_template('index.html', jumlahcust=jumlahcust, total=formatted_total, data=data)


@app.route('/forms')
def forms():
    return render_template('forms.html')


@app.route('/charts')
def charts():
    cur = get_db().cursor()

    cur.execute("SELECT COUNT(DISTINCT customer_name) FROM penjualan")
    jumlahcust = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(purchase_amount), 0) FROM penjualan WHERE payment_status != 'failed'")
    total = cur.fetchone()[0]
    formatted_total = format_number(total)

    cur.execute("SELECT COUNT(*) FROM penjualan")
    jumlahtrx = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM penjualan WHERE payment_status != 'failed'")
    success_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM penjualan WHERE payment_status = 'failed'")
    failed_count = cur.fetchone()[0]

    return render_template('charts.html',
                           jumlahcust=jumlahcust,
                           total=formatted_total,
                           jumlahtrx=jumlahtrx,
                           success_count=success_count,
                           failed_count=failed_count)


@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    cur = get_db().cursor()

    if keyword:
        sql = "SELECT id, customer_name, purchase_amount, payment_status, date, note FROM penjualan WHERE customer_name LIKE ? ORDER BY date DESC"
        cur.execute(sql, (f"%{keyword}%",))
    else:
        sql = "SELECT id, customer_name, purchase_amount, payment_status, date, note FROM penjualan ORDER BY date DESC"
        cur.execute(sql)

    results = cur.fetchall()
    return render_template('search.html', results=results)


# ─── API Routes ──────────────────────────────────────────────────────
@app.route('/api/submit', methods=['POST'])
def submit_form():
    data = request.get_json()
    db = get_db()
    cur = db.cursor()
    sql = "INSERT INTO penjualan (customer_name, date, purchase_amount, payment_status, note) VALUES (?, ?, ?, ?, ?)"
    values = (data['name'], data['tanggal'], data['purchase'], data['selectedOption'], data['note'])
    cur.execute(sql, values)
    db.commit()
    return jsonify({'message': 'Entry submitted successfully'})


@app.route('/api/penjualan', methods=['GET'])
def get_penjualan():
    cur = get_db().cursor()
    # SQLite strftime for 'dd/mm/yyyy' -> %d/%m/%Y
    query = """SELECT strftime('%d/%m/%Y', date) AS formatted_date,
               SUM(purchase_amount)
               FROM penjualan
               WHERE payment_status != 'failed'
               GROUP BY date
               ORDER BY date"""
    cur.execute(query)
    data = cur.fetchall()
    result = [{'nama': row[0], 'total_penjualan': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/failed', methods=['GET'])
def get_failed():
    cur = get_db().cursor()
    query = "SELECT id, SUM(purchase_amount) FROM penjualan WHERE payment_status = 'failed' GROUP BY id"
    cur.execute(query)
    data = cur.fetchall()
    result = [{'nama': row[0], 'total_penjualan': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/top_customers', methods=['GET'])
def top_customers():
    cur = get_db().cursor()
    query = """SELECT customer_name, SUM(purchase_amount) AS total
               FROM penjualan
               WHERE payment_status != 'failed'
               GROUP BY customer_name
               ORDER BY total DESC
               LIMIT 6"""
    cur.execute(query)
    data = cur.fetchall()
    result = [{'name': row[0], 'total': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/delete', methods=['POST'])
def delete_data():
    data = request.get_json(silent=True) or {}
    customer_id = data.get('customer')
    if customer_id is None:
        return jsonify({'error': 'No customer ID provided'}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM penjualan WHERE id = ?", (customer_id,))
    db.commit()
    return jsonify({'message': 'Data deleted successfully'})


# ─── Run ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')