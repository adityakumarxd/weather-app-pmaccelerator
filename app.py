from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv('OPENWEATHER_API_KEY') or 'YOUR_OPENWEATHERMAP_API_KEY'


def get_location_coordinates(query):
    """Resolve location query (city name, postal code, etc.) to lat/lon using OpenWeatherMap Geocoding API"""
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=1&appid={API_KEY}"
    response = requests.get(geo_url)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return data['lat'], data['lon'], data.get('name'), data.get('state'), data.get('country')
    return None, None, None, None, None


def fetch_weather(lat, lon):
    """Fetch current weather and 5-day forecast using One Call API"""
    weather_url = f"https://api.openweathermap.org/data/2.5/onecall"
    params = {
        'lat': lat,
        'lon': lon,
        'units': 'metric',
        'exclude': 'minutely,hourly,alerts',
        'appid': API_KEY
    }
    response = requests.get(weather_url, params=params)
    if response.status_code == 200:
        return response.json()
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    location_info = None
    error_message = None

    if request.method == 'POST':
        location_query = request.form.get('location')

        if not location_query:
            error_message = "Please enter a location."
        else:
            lat, lon, name, state, country = get_location_coordinates(location_query)
            if lat is None:
                error_message = "Location not found. Please enter a valid location."
            else:
                weather_data = fetch_weather(lat, lon)
                if weather_data is None:
                    error_message = "Weather data unavailable for this location."
                else:
                    location_info = {
                        'name': name,
                        'state': state,
                        'country': country
                    }

    return render_template('index.html', weather=weather_data, location=location_info, error=error_message)


@app.route('/geolocate')
def geolocate():
    """Endpoint to fetch weather info by lat/lon query params via JS geolocation"""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates'}), 400

    weather_data = fetch_weather(lat, lon)
    if not weather_data:
        return jsonify({'error': 'Weather data unavailable'}), 500

    return jsonify(weather_data)


if __name__ == '__main__':
    app.run(debug=True)
