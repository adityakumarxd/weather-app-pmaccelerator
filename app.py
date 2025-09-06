import os
import csv
import json
import requests
from datetime import datetime
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'devsecret')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'weather.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')  # Optional for videos

# Models

class WeatherQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(120), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    weather_data = db.Column(db.Text, nullable=False)  # Store raw JSON string
    
    def __repr__(self):
        return f'<WeatherQuery {self.location} from {self.start_date} to {self.end_date}>'

# Helpers

def validate_dates(start_str, end_str):
    try:
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
        if start > end:
            return False, "Start date must be before or equal to end date."
        return True, (start, end)
    except Exception:
        return False, "Invalid date format. Use YYYY-MM-DD."

def validate_location(location):
    # Use OpenWeatherMap Geocoding API for validation
    geocode_url = f'http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}'
    res = requests.get(geocode_url)
    if res.status_code == 200 and len(res.json()) > 0:
        return True, res.json()[0]  # return first matched location
    return False, None

def fetch_weather(lat, lon, start_date, end_date):
    # OpenWeatherMap free tier doesn't support historical data.
    # So as demo, we call current weather API (can extend with paid or other services).
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def fetch_youtube_video(location):
    if not YOUTUBE_API_KEY:
        return None
    search_url = ('https://www.googleapis.com/youtube/v3/search'
                  f'?part=snippet&q={location}+travel&key={YOUTUBE_API_KEY}&type=video&maxResults=1')
    res = requests.get(search_url)
    if res.status_code == 200:
        items = res.json().get('items')
        if items:
            return f"<https://www.youtube.com/embed/{items>[0]['id']['videoId']}"
    return None

# Routes

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    video_url = None
    error = None
    
    if request.method == 'POST':
        location = request.form.get('location').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        # Validate dates
        valid, dates_or_msg = validate_dates(start_date_str, end_date_str)
        if not valid:
            flash(dates_or_msg, 'error')
            return redirect(url_for('index'))

        start_date, end_date = dates_or_msg

        # Validate location
        is_valid_loc, geo_data = validate_location(location)
        if not is_valid_loc:
            flash('Location not found. Please enter a valid location.', 'error')
            return redirect(url_for('index'))
        
        # Fetch weather (demo limited to current weather)
        weather_json = fetch_weather(geo_data['lat'], geo_data['lon'], start_date, end_date)
        if not weather_json:
            flash('Error retrieving weather data. Try again later.', 'error')
            return redirect(url_for('index'))
        
        # Save query & weather_data
        wq = WeatherQuery(
            location=location,
            start_date=start_date,
            end_date=end_date,
            weather_data=json.dumps(weather_json)
        )
        db.session.add(wq)
        db.session.commit()
        
        weather_data = weather_json
        video_url = fetch_youtube_video(location)

    return render_template('index.html', weather=weather_data, video_url=video_url)

@app.route('/history')
def history():
    queries = WeatherQuery.query.order_by(WeatherQuery.id.desc()).all()
    # Parse the JSON string for each query ahead of template rendering
    for q in queries:
        try:
            q.parsed_weather = json.loads(q.weather_data)
        except Exception:
            q.parsed_weather = None
    return render_template('history.html', queries=queries)

@app.route('/update/<int:query_id>', methods=['GET', 'POST'])
def update(query_id):
    query = WeatherQuery.query.get_or_404(query_id)
    error = None

    if request.method == 'POST':
        location = request.form.get('location').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        valid, dates_or_msg = validate_dates(start_date_str, end_date_str)
        if not valid:
            error = dates_or_msg
        else:
            start_date, end_date = dates_or_msg
            is_valid_loc, geo_data = validate_location(location)
            if not is_valid_loc:
                error = 'Location validation failed.'
            else:
                weather_json = fetch_weather(geo_data['lat'], geo_data['lon'], start_date, end_date)
                if not weather_json:
                    error = 'Weather API error.'
                else:
                    query.location = location
                    query.start_date = start_date
                    query.end_date = end_date
                    query.weather_data = json.dumps(weather_json)
                    db.session.commit()
                    flash('Updated successfully!', 'success')
                    return redirect(url_for('history'))

    return render_template('update.html', query=query, error=error)

@app.route('/delete/<int:query_id>', methods=['POST'])
def delete(query_id):
    query = WeatherQuery.query.get_or_404(query_id)
    db.session.delete(query)
    db.session.commit()
    flash('Entry deleted.', 'info')
    return redirect(url_for('history'))

@app.route('/export/<string:export_format>')
def export_data(export_format):
    queries = WeatherQuery.query.all()
    
    if export_format == 'json':
        data = [{
            'id': q.id,
            'location': q.location,
            'start_date': q.start_date.isoformat(),
            'end_date': q.end_date.isoformat(),
            'weather_data': json.loads(q.weather_data)
        } for q in queries]
        response = Response(json.dumps(data, indent=2), mimetype='application/json')
        response.headers.set("Content-Disposition", "attachment", filename="weather_data.json")
        return response
    
    elif export_format == 'csv':
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['ID', 'Location', 'Start Date', 'End Date', 'Temperature (C)', 'Weather Description'])
        for q in queries:
            weather = json.loads(q.weather_data)
            writer.writerow([
                q.id,
                q.location,
                q.start_date.isoformat(),
                q.end_date.isoformat(),
                weather.get('main', {}).get('temp', ''),
                weather.get('weather', [{}])[0].get('description', '')
            ])
        output = si.getvalue()
        response = Response(output, mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename="weather_data.csv")
        return response

    return redirect(url_for('history'))

@app.route('/map/<location>')
def show_map(location):
    # Embed Google Maps iframe with search for location
    map_url = f"https://www.google.com/maps/embed/v1/place?key={os.environ.get('GOOGLE_MAPS_API_KEY')}&q={location.replace(' ', '+')}"
    return render_template('map.html', map_url=map_url, location=location)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
