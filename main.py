from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     name TEXT,
     email TEXT UNIQUE,
     birth_date TEXT,
     birth_time TEXT,
     birth_place TEXT,
     sun_sign TEXT,
     moon_sign TEXT,
     rising_sign TEXT)
''')
conn.commit()

# Simple Sun sign calculation
def get_sun_sign(birth_date):
    birth_date = birth_date.replace('/', '-')
    parts = birth_date.split('-')
    if len(parts) != 3:
        return 'Unknown'
    month = int(parts[1])
    day = int(parts[2])

    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return 'Aries'
    if (month == 4 and day >= 20) or (month == 5 and day <= 20): return 'Taurus'
    if (month == 5 and day >= 21) or (month == 6 and day <= 20): return 'Gemini'
    if (month == 6 and day >= 21) or (month == 7 and day <= 22): return 'Cancer'
    if (month == 7 and day >= 23) or (month == 8 and day <= 22): return 'Leo'
    if (month == 8 and day >= 23) or (month == 9 and day <= 22): return 'Virgo'
    if (month == 9 and day >= 23) or (month == 10 and day <= 22): return 'Libra'
    if (month == 10 and day >= 23) or (month == 11 and day <= 21): return 'Scorpio'
    if (month == 11 and day >= 22) or (month == 12 and day <= 21): return 'Sagittarius'
    if (month == 12 and day >= 22) or (month == 1 and day <= 19): return 'Capricorn'
    if (month == 1 and day >= 20) or (month == 2 and day <= 18): return 'Aquarius'
    if (month == 2 and day >= 19) or (month == 3 and day <= 20): return 'Pisces'
    return 'Unknown'

# Placeholders for Moon and Rising (update later with API)
def get_moon_sign():
    return 'Cancer'

def get_rising_sign():
    return 'Leo'

def compatibility_score(user1, user2):
    elements = {
        'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
        'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
        'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
        'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
    }
    score = 0
    if elements.get(user1.get('sun_sign')) == elements.get(user2.get('sun_sign')): score += 40
    if elements.get(user1.get('moon_sign')) == elements.get(user2.get('moon_sign')): score += 30
    if elements.get(user1.get('rising_sign')) == elements.get(user2.get('rising_sign')): score += 30
    return score

@app.route('/')
def home():
    return "Astro Dating API is running and healthy 🚀", 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data received"}), 400

    name        = data.get('name')
    email       = data.get('email')
    birth_date  = data.get('birthDate')
    birth_time  = data.get('birthTime')
    birth_place = data.get('birthPlace')

    if not all([name, email, birth_date, birth_time, birth_place]):
        return jsonify({"error": "Missing required fields"}), 400

    sun_sign   = get_sun_sign(birth_date)
    moon_sign  = get_moon_sign()
    rising_sign = get_rising_sign()

    try:
        cursor.execute('''
            INSERT INTO users
            (name, email, birth_date, birth_time, birth_place, sun_sign, moon_sign, rising_sign)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, birth_date, birth_time, birth_place, sun_sign, moon_sign, rising_sign))
        
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 400
    
    return jsonify({
        "message": "User registered successfully",
        "id": new_id,
        "signs": {"sun": sun_sign, "moon": moon_sign, "rising": rising_sign}
    }), 201

@app.route('/match/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data = {
        'sun_sign':   user[6],
        'moon_sign':  user[7],
        'rising_sign': user[8]
    }
    
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    others = cursor.fetchall()
    
    matches = []
    for other in others:
        other_data = {
            'sun_sign':   other[6],
            'moon_sign':  other[7],
            'rising_sign': other[8]
        }
        score = compatibility_score(user_data, other_data)
        
        if score > 50:
            matches.append({
                'name': other[1],
                'score': score,
                'id': other[0]
            })
    
    return jsonify({"matches": matches, "count": len(matches)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
