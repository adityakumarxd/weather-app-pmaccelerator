import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

API_KEY = os.environ.get('OPENWEATHER_API_KEY')

def get_weather(city):
    url = (
        f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    error = None
    if request.method == 'POST':
        city = request.form['city']
        weather = get_weather(city)
        if not weather:
            error = 'Could not fetch weather for this location. Please try again.'
    return render_template('index.html', weather=weather, error=error)

if __name__ == '__main__':
    app.run(debug=True)
