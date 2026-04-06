import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ─── Database Configuration ─────────────────────────────────────────
# Uses environment variables for production (Render + Aiven).
# Falls back to localhost defaults for local development.
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'datapenjualan')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', '3306'))

# SSL required for Aiven cloud MySQL
import MySQLdb
ssl_mode = os.environ.get('MYSQL_SSL', '')
if ssl_mode:
    app.config['MYSQL_CUSTOM_OPTIONS'] = {"ssl": {"ca": ssl_mode}}

from flask_mysqldb import MySQL
db = MySQL(app)


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
    cur = db.connection.cursor()

    # Count unique customers
    cur.execute("SELECT COUNT(DISTINCT customer_name) FROM penjualan")
    jumlahcust = cur.fetchone()[0]

    # Total sales (excluding failed)
    cur.execute("SELECT COALESCE(SUM(purchase_amount), 0) FROM penjualan WHERE payment_status != 'failed'")
    total = cur.fetchone()[0]
    formatted_total = format_number(total)

    # Recent 5 transactions
    cur.execute("SELECT id, customer_name, purchase_amount, payment_status, date FROM penjualan ORDER BY date DESC LIMIT 5")
    data = cur.fetchall()

    cur.close()
    return render_template('index.html', jumlahcust=jumlahcust, total=formatted_total, data=data)


@app.route('/forms')
def forms():
    return render_template('forms.html')


@app.route('/charts')
def charts():
    cur = db.connection.cursor()

    # Total customers
    cur.execute("SELECT COUNT(DISTINCT customer_name) FROM penjualan")
    jumlahcust = cur.fetchone()[0]

    # Total sales (excluding failed)
    cur.execute("SELECT COALESCE(SUM(purchase_amount), 0) FROM penjualan WHERE payment_status != 'failed'")
    total = cur.fetchone()[0]
    formatted_total = format_number(total)

    # Total transactions
    cur.execute("SELECT COUNT(*) FROM penjualan")
    jumlahtrx = cur.fetchone()[0]

    # Success count
    cur.execute("SELECT COUNT(*) FROM penjualan WHERE payment_status != 'failed'")
    success_count = cur.fetchone()[0]

    # Failed count
    cur.execute("SELECT COUNT(*) FROM penjualan WHERE payment_status = 'failed'")
    failed_count = cur.fetchone()[0]

    cur.close()
    return render_template('charts.html',
                           jumlahcust=jumlahcust,
                           total=formatted_total,
                           jumlahtrx=jumlahtrx,
                           success_count=success_count,
                           failed_count=failed_count)


@app.route('/search')
def search():
    """Search page — query parameter 'q' is optional.
    If provided, filter by customer_name LIKE %q%.
    If empty, return all records."""
    keyword = request.args.get('q', '').strip()
    cur = db.connection.cursor()

    if keyword:
        sql = "SELECT id, customer_name, purchase_amount, payment_status, date, note FROM penjualan WHERE customer_name LIKE %s ORDER BY date DESC"
        cur.execute(sql, (f"%{keyword}%",))
    else:
        sql = "SELECT id, customer_name, purchase_amount, payment_status, date, note FROM penjualan ORDER BY date DESC"
        cur.execute(sql)

    results = cur.fetchall()
    cur.close()
    return render_template('search.html', results=results)


# ─── API Routes ──────────────────────────────────────────────────────
@app.route('/api/submit', methods=['POST'])
def submit_form():
    """Insert a new transaction entry."""
    data = request.get_json()
    cur = db.connection.cursor()
    sql = "INSERT INTO penjualan (customer_name, date, purchase_amount, payment_status, note) VALUES (%s, %s, %s, %s, %s)"
    values = (data['name'], data['tanggal'], data['purchase'], data['selectedOption'], data['note'])
    cur.execute(sql, values)
    db.connection.commit()
    cur.close()
    return jsonify({'message': 'Entry submitted successfully'})


@app.route('/api/penjualan', methods=['GET'])
def get_penjualan():
    """Get daily sales totals (successful only), grouped by date."""
    cur = db.connection.cursor()
    query = """SELECT DATE_FORMAT(date, '%%d/%%m/%%Y') AS formatted_date,
               SUM(purchase_amount)
               FROM penjualan
               WHERE payment_status != 'failed'
               GROUP BY date
               ORDER BY date"""
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    result = [{'nama': row[0], 'total_penjualan': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/failed', methods=['GET'])
def get_failed():
    """Get failed transaction totals, grouped by id."""
    cur = db.connection.cursor()
    query = "SELECT id, SUM(purchase_amount) FROM penjualan WHERE payment_status = 'failed' GROUP BY id"
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    result = [{'nama': row[0], 'total_penjualan': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/top_customers', methods=['GET'])
def top_customers():
    """Get top 6 customers by total purchase amount (successful only)."""
    cur = db.connection.cursor()
    query = """SELECT customer_name, SUM(purchase_amount) AS total
               FROM penjualan
               WHERE payment_status != 'failed'
               GROUP BY customer_name
               ORDER BY total DESC
               LIMIT 6"""
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    result = [{'name': row[0], 'total': float(row[1])} for row in data]
    return jsonify(result)


@app.route('/api/delete', methods=['POST'])
def delete_data():
    """Delete a transaction by ID."""
    customer_id = request.json.get('customer')
    cur = db.connection.cursor()
    cur.execute("DELETE FROM penjualan WHERE id = %s", (customer_id,))
    db.connection.commit()
    cur.close()
    return jsonify({'message': 'Data deleted successfully'})


# ─── Run ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')