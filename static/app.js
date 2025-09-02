document.addEventListener('DOMContentLoaded', function () {
    const useGeoBtn = document.getElementById('useGeoBtn');
    const weatherResult = document.getElementById('weatherResult');
    const infoBtn = document.getElementById('infoBtn');
    const infoModal = document.getElementById('infoModal');
    const closeModal = document.getElementById('closeModal');

    // Geolocation button click
    useGeoBtn.addEventListener('click', () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                try {
                    const response = await fetch(`/geolocate?lat=${lat}&lon=${lon}`);
                    if (!response.ok) throw new Error('Network response was not ok');
                    const data = await response.json();

                    // Render the weather result dynamically
                    renderWeather(data);
                } catch (error) {
                    alert('Failed to load weather data for your location');
                    console.error(error);
                }
            }, () => {
                alert('Permission denied or unable to get location.');
            });
        } else {
            alert('Geolocation is not supported by your browser.');
        }
    });

    // Info modal open/close
    infoBtn.addEventListener('click', () => {
        infoModal.classList.remove('hidden');
    });

    closeModal.addEventListener('click', () => {
        infoModal.classList.add('hidden');
    });

    window.addEventListener('click', (event) => {
        if (event.target === infoModal) {
            infoModal.classList.add('hidden');
        }
    });

    function renderWeather(weather) {
        if (!weather) return;

        // Clear previous weather result if any
        if (weatherResult) {
            weatherResult.innerHTML = '';
            weatherResult.classList.remove('hidden');
        } else {
            return;
        }

        // Build current weather overview
        const current = weather.current;
        const locationTitle = document.createElement('h2');
        locationTitle.textContent = 'Current Location Weather';

        const icon = document.createElement('img');
        icon.src = `https://openweathermap.org/img/wn/${current.weather[0].icon}@2x.png`;
        icon.alt = current.weather[0].description;

        const description = document.createElement('p');
        description.textContent = current.weather[0].description;

        const temp = document.createElement('p');
        temp.textContent = `Temperature: ${current.temp.toFixed(1)} °C`;

        const humidity = document.createElement('p');
        humidity.textContent = `Humidity: ${current.humidity}%`;

        const wind = document.createElement('p');
        wind.textContent = `Wind Speed: ${current.wind_speed} m/s`;

        const overviewDiv = document.createElement('div');
        overviewDiv.classList.add('weather-overview');
        overviewDiv.appendChild(locationTitle);
        overviewDiv.appendChild(icon);
        overviewDiv.appendChild(description);
        overviewDiv.appendChild(temp);
        overviewDiv.appendChild(humidity);
        overviewDiv.appendChild(wind);

        weatherResult.appendChild(overviewDiv);

        // Build 5-day forecast
        const forecastTitle = document.createElement('h3');
        forecastTitle.textContent = '5-Day Forecast';
        weatherResult.appendChild(forecastTitle);

        const forecastDiv = document.createElement('div');
        forecastDiv.classList.add('forecast');

        for (let i = 1; i <= 5; i++) {
            const day = weather.daily[i];
            const date = new Date(day.dt * 1000);
            const dayName = date.toLocaleDateString(undefined, { weekday: 'short' });

            const dayDiv = document.createElement('div');
            dayDiv.classList.add('forecast-day');

            const dayNameEl = document.createElement('h4');
            dayNameEl.textContent = dayName;

            const dayIcon = document.createElement('img');
            dayIcon.src = `https://openweathermap.org/img/wn/${day.weather[0].icon}@2x.png`;
            dayIcon.alt = day.weather[0].description;

            const dayTemp = document.createElement('p');
            dayTemp.textContent = `${day.temp.max.toFixed(1)}° / ${day.temp.min.toFixed(1)}°C`;

            dayDiv.appendChild(dayNameEl);
            dayDiv.appendChild(dayIcon);
            dayDiv.appendChild(dayTemp);

            forecastDiv.appendChild(dayDiv);
        }

        weatherResult.appendChild(forecastDiv);
    }
});
