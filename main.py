from flask import Flask, request, jsonify
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
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
     birth_date TEXT,
     birth_time TEXT,
     birth_place TEXT,
     sun_sign TEXT,
     moon_sign TEXT,
     rising_sign TEXT)
''')
conn.commit()

def get_astrology_signs(birth_date, birth_time, lat, lon):
    dt = Datetime(birth_date, birth_time, 0)  # UTC offset 0
    pos = GeoPos(lat, lon)
    chart = Chart(dt, pos)
    sun   = chart.get(const.SUN)
    moon  = chart.get(const.MOON)
    asc   = chart.get(const.ASC)
    return sun.sign, moon.sign, asc.sign

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
    birth_date  = data.get('birthDate')
    birth_time  = data.get('birthTime')
    birth_place = data.get('birthPlace')

    if not all([name, birth_date, birth_time, birth_place]):
        return jsonify({"error": "Missing required fields"}), 400

    lat, lon = 26.3184, -80.0998  # Deerfield Beach / Parkland area

    try:
        sun, moon, rising = get_astrology_signs(birth_date, birth_time, lat, lon)
    except Exception as e:
        return jsonify({"error": f"Chart calculation failed: {str(e)}"}), 500

    cursor.execute('''
        INSERT INTO users
        (name, birth_date, birth_time, birth_place, sun_sign, moon_sign, rising_sign)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, birth_date, birth_time, birth_place, sun, moon, rising))
    
    conn.commit()
    new_id = cursor.lastrowid
    
    return jsonify({
        "message": "User registered successfully",
        "id": new_id,
        "signs": {"sun": sun, "moon": moon, "rising": rising}
    }), 201

@app.route('/match/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data = {
        'sun_sign':   user[5],
        'moon_sign':  user[6],
        'rising_sign': user[7]
    }
    
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    others = cursor.fetchall()
    
    matches = []
    for other in others:
        other_data = {
            'sun_sign':   other[5],
            'moon_sign':  other[6],
            'rising_sign': other[7]
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
