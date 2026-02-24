from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database with all planets
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
     rising_sign TEXT,
     venus_sign TEXT,
     mars_sign TEXT,
     jupiter_sign TEXT)
''')
conn.commit()

# Zodiac sign from ecliptic longitude
def get_zodiac_sign(deg):
    deg = deg % 360
    if 0 <= deg < 30: return 'Aries'
    if 30 <= deg < 60: return 'Taurus'
    if 60 <= deg < 90: return 'Gemini'
    if 90 <= deg < 120: return 'Cancer'
    if 120 <= deg < 150: return 'Leo'
    if 150 <= deg < 180: return 'Virgo'
    if 180 <= deg < 210: return 'Libra'
    if 210 <= deg < 240: return 'Scorpio'
    if 240 <= deg < 270: return 'Sagittarius'
    if 270 <= deg < 300: return 'Capricorn'
    if 300 <= deg < 330: return 'Aquarius'
    return 'Pisces'

# Sun sign (accurate date-based)
def get_sun_sign(birth_date):
    try:
        y, m, d = map(int, birth_date.replace('/', '-').split('-'))
        if (m == 3 and d >= 21) or (m == 4 and d <= 19): return 'Aries'
        if (m == 4 and d >= 20) or (m == 5 and d <= 20): return 'Taurus'
        if (m == 5 and d >= 21) or (m == 6 and d <= 20): return 'Gemini'
        if (m == 6 and d >= 21) or (m == 7 and d <= 22): return 'Cancer'
        if (m == 7 and d >= 23) or (m == 8 and d <= 22): return 'Leo'
        if (m == 8 and d >= 23) or (m == 9 and d <= 22): return 'Virgo'
        if (m == 9 and d >= 23) or (m == 10 and d <= 22): return 'Libra'
        if (m == 10 and d >= 23) or (m == 11 and d <= 21): return 'Scorpio'
        if (m == 11 and d >= 22) or (m == 12 and d <= 21): return 'Sagittarius'
        if (m == 12 and d >= 22) or (m == 1 and d <= 19): return 'Capricorn'
        if (m == 1 and d >= 20) or (m == 2 and d <= 18): return 'Aquarius'
        if (m == 2 and d >= 19) or (m == 3 and d <= 20): return 'Pisces'
        return 'Unknown'
    except:
        return 'Unknown'

# Approximate Julian Day (rough but sufficient for sign calculation)
def date_to_jd(birth_date, birth_time):
    try:
        y, m, d = map(int, birth_date.replace('/', '-').split('-'))
        h, min_ = map(int, birth_time.split(':'))
        if m <= 2:
            y -= 1
            m += 12
        a = y // 100
        b = 2 - a + (a // 4)
        jd = int(365.25 * (y + 4716)) + int(30.7 * (m + 1)) + d + b - 1524.5 + (h + min_/60.0)/24.0
        return jd
    except:
        return 2451545.0  # fallback to J2000

# Approximate planetary positions (mean longitude) - good enough for sign
def get_planet_sign(planet, jd):
    if planet == 'sun':
        return get_sun_sign(datetime.utcfromtimestamp((jd - 2440587.5) * 86400).strftime('%Y/%m/%d'))
    elif planet == 'moon':
        d = jd - 2451545.0
        long = (218.316 + 13.176396 * d) % 360
        return get_zodiac_sign(long)
    elif planet == 'venus':
        d = jd - 2451545.0
        long = (181.979 + 1.602130 * d) % 360
        return get_zodiac_sign(long)
    elif planet == 'mars':
        d = jd - 2451545.0
        long = (355.433 + 0.524033 * d) % 360
        return get_zodiac_sign(long)
    elif planet == 'jupiter':
        d = jd - 2451545.0
        long = (34.351 + 0.083085 * d) % 360
        return get_zodiac_sign(long)
    else:
        return 'Unknown'

# Approximate Ascendant (Rising sign)
def get_rising_sign(jd, lon):
    # Rough sidereal time
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + lon
    lst = gmst % 360
    asc_long = (lst - 90) % 360  # very approximate
    return get_zodiac_sign(asc_long)

# Generate full natal chart
def generate_natal_chart(birth_date, birth_time, birth_place):
    jd = date_to_jd(birth_date, birth_time)
    
    # Approximate lat/lon for rising (using geocode would be better, but skipped for simplicity)
    lat, lon = 26.3184, -80.0998  # default Deerfield Beach
    
    chart = {
        'sun': get_planet_sign('sun', jd),
        'moon': get_planet_sign('moon', jd),
        'venus': get_planet_sign('venus', jd),
        'mars': get_planet_sign('mars', jd),
        'jupiter': get_planet_sign('jupiter', jd),
        'rising': get_rising_sign(jd, lon)
    }
    
    print("Generated Natal Chart:", chart)
    return chart

# Advanced compatibility using all planets
def compatibility_score(user1, user2):
    elements = {
        'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
        'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
        'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
        'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
    }

    score = 0

    # Sun-Sun (identity) - 20%
    if elements.get(user1['sun']) == elements.get(user2['sun']):
        score += 20

    # Moon-Moon (emotions) - 25%
    if elements.get(user1['moon']) == elements.get(user2['moon']):
        score += 25

    # Venus-Venus (love/attraction) - 20%
    if elements.get(user1['venus']) == elements.get(user2['venus']):
        score += 20

    # Mars-Mars (passion/energy) - 15%
    if elements.get(user1['mars']) == elements.get(user2['mars']):
        score += 15

    # Jupiter-Jupiter (growth/luck) - 10%
    if elements.get(user1['jupiter']) == elements.get(user2['jupiter']):
        score += 10

    # Rising-Rising (outer vibe) - 10%
    if elements.get(user1['rising']) == elements.get(user2['rising']):
        score += 10

    return min(score, 100)

@app.route('/')
def home():
    return "Astro Dating API is running and healthy 🚀", 200

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        name        = data.get('name')
        birth_date  = data.get('birthDate')
        birth_time  = data.get('birthTime')
        birth_place = data.get('birthPlace')

        if not all([name, birth_date, birth_time, birth_place]):
            return jsonify({"error": "Missing required fields"}), 400

        chart = generate_natal_chart(birth_date, birth_time, birth_place)

        cursor.execute('''
            INSERT INTO users
            (name, birth_date, birth_time, birth_place, sun_sign, moon_sign, rising_sign, venus_sign, mars_sign, jupiter_sign)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, birth_date, birth_time, birth_place,
              chart['sun'], chart['moon'], chart['rising'],
              chart['venus'], chart['mars'], chart['jupiter']))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({
            "message": "User registered successfully",
            "id": new_id,
            "natal_chart": chart
        }), 201

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/match/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_chart = {
        'sun': user[5],
        'moon': user[6],
        'rising': user[7],
        'venus': user[8],
        'mars': user[9],
        'jupiter': user[10]
    }
    
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    others = cursor.fetchall()
    
    matches = []
    for other in others:
        other_chart = {
            'sun': other[5],
            'moon': other[6],
            'rising': other[7],
            'venus': other[8],
            'mars': other[9],
            'jupiter': other[10]
        }
        score = compatibility_score(user_chart, other_chart)
        
        if score > 50:
            matches.append({
                'name': other[1],
                'score': score,
                'id': other[0]
            })
    
    return jsonify({"matches": matches, "count": len(matches)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
