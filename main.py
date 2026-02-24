from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS
import requests

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
     rising_sign TEXT,
     venus_sign TEXT,
     mars_sign TEXT,
     jupiter_sign TEXT)
''')
conn.commit()

# Get lat/lon from birth_place using free geocode API (handles all countries)
def get_lat_lon(birth_place):
    url = f"https://nominatim.openstreetmap.org/search?q={birth_place}&format=json&limit=1"
    headers = {'User-Agent': 'AstroDatingApp/1.0'}
    try:
        resp = requests.get(url, headers=headers).json()
        if resp:
            return float(resp[0]['lat']), float(resp[0]['lon'])
    except:
        pass
    # Fallback to Deerfield Beach, FL
    return 26.3184, -80.0998

# Zodiac sign from longitude
def get_zodiac_sign(longitude):
    deg = longitude % 360
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

# Draft natal chart (positions of planets)
def get_natal_chart(birth_date, birth_time, lat, lon):
    # Use approximate formulas - for full accuracy, use API
    # Print the chart for debugging
    print("Natal Chart for: ", birth_date, birth_time, lat, lon)
    
    # Sun: simple date-based
    sun_sign = get_sun_sign(birth_date)
    
    # Moon: approximate longitude (Meeus-inspired, rough)
    # J0 = 2451545.0 (2000 Jan 1.5)
    jd = date_to_jd(birth_date, birth_time)
    d = jd - 2451545.0
    moon_long = (218.32 + 13.176396 * d) % 360  # Approximate mean longitude
    moon_sign = get_zodiac_sign(moon_long)
    
    # Venus: approximate (orbital period 224.7 days, mean longitude)
    venus_long = (181.98 + 1.602130 * d) % 360
    venus_sign = get_zodiac_sign(venus_long)
    
    # Mars: approximate (687 days)
    mars_long = (355.43 + 0.524033 * d) % 360
    mars_sign = get_zodiac_sign(mars_long)
    
    # Jupiter: approximate (4332 days)
    jupiter_long = (34.35 + 0.0829 * d) % 360
    jupiter_sign = get_zodiac_sign(jupiter_long)
    
    # Ascendant: approximate sidereal time
    lst = jd_to_lst(jd, lon)
    asc_long = (lst - 90) % 360
    rising_sign = get_zodiac_sign(asc_long)
    
    chart = {
        'sun': sun_sign,
        'moon': moon_sign,
        'venus': venus_sign,
        'mars': mars_sign,
        'jupiter': jupiter_sign,
        'rising': rising_sign
    }
    
    print("Chart Positions:", chart)
    
    return chart

# Helper: Date to Julian Day (rough)
def date_to_jd(birth_date, birth_time):
    y, m, d = map(int, birth_date.split('/'))
    h, mm = map(int, birth_time.split(':'))
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    jd = int(365.25 * (y + 4716)) + int(30.7 * (m + 1)) + d + b - 1524.5 + (h + mm/60)/24
    return jd

# Helper: JD to Local Sidereal Time (rough)
def jd_to_lst(jd, lon):
    s0 = jd - 2451545.0
    s = 280.46061837 + 360.98564736629 * s0 + lon
    return s % 360

# Compatibility using all planets
def compatibility_score(user1, user2):
    elements = {
        'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
        'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
        'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
        'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
    }

    score = 0

    # Sun-Sun element (20%)
    if elements.get(user1['sun']) == elements.get(user2['sun']):
        score += 20

    # Moon-Moon emotional (20%)
    if elements.get(user1['moon']) == elements.get(user2['moon']):
        score += 20

    # Venus-Venus love (15%)
    if elements.get(user1['venus']) == elements.get(user2['venus']):
        score += 15

    # Mars-Mars energy (15%)
    if elements.get(user1['mars']) == elements.get(user2['mars']):
        score += 15

    # Jupiter-Jupiter growth (15%)
    if elements.get(user1['jupiter']) == elements.get(user2['jupiter']):
        score += 15

    # Rising-Rising outer (15%)
    if elements.get(user1['rising']) == elements.get(user2['rising']):
        score += 15

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

    lat, lon = get_lat_lon(birth_place)
    chart = get_natal_chart(birth_date, birth_time, lat, lon)

    cursor.execute('''
        INSERT INTO users
        (name, birth_date, birth_time, birth_place, sun_sign, moon_sign, rising_sign, venus_sign, mars_sign, jupiter_sign)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, birth_date, birth_time, birth_place, chart['sun'], chart['moon'], chart['rising'], chart['venus'], chart['mars'], chart['jupiter']))
    
    conn.commit()
    
    new_id = cursor.lastrowid
    
    return jsonify({
        "message": "User registered successfully",
        "id": new_id,
        "signs": chart
    }), 201

@app.route('/match/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data = {
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
        other_data = {
            'sun': other[5],
            'moon': other[6],
            'rising': other[7],
            'venus': other[8],
            'mars': other[9],
            'jupiter': other[10]
        }
        score = compatibility_score(user_data, other_data)
        
        if score > 50:
            matches.append({
                'name': other[1],
                'score': score,
                'id': other[0]
            })
    
    return jsonify({
        "matches": matches,
        "count": len(matches)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
