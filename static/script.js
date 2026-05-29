const apiEndpoint = document.body.dataset.apiEndpoint;
const cityForm = document.getElementById('weatherForm');
const cityInput = document.getElementById('cityInput');
const searchButton = document.getElementById('searchButton');
const errorMessage = document.getElementById('errorMessage');
const cityName = document.getElementById('cityName');
const currentTime = document.getElementById('currentDateTime');
const weatherDescription = document.getElementById('weatherDescription');
const weatherIcon = document.getElementById('weatherIcon');
const weatherIconAlt = document.getElementById('weatherIconAlt');
const temperature = document.getElementById('temperature');
const feelsLike = document.getElementById('feelsLike');
const humidity = document.getElementById('humidity');
const windSpeed = document.getElementById('windSpeed');
const weatherCondition = document.getElementById('weatherCondition');
const localTime = document.getElementById('localTime');
const forecastCards = document.getElementById('forecastCards');
const loadingState = document.getElementById('loadingState');

function setLoading(isLoading) {
  searchButton.disabled = isLoading;
  loadingState.classList.toggle('is-visible', isLoading);
  searchButton.innerHTML = isLoading
    ? '<span class="button-spinner"></span> Loading...'
    : 'Search';
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.add('is-visible');
}

function clearError() {
  errorMessage.textContent = '';
  errorMessage.classList.remove('is-visible');
}

function updateClock() {
  const now = new Date();
  currentTime.textContent = now.toLocaleString([], {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  });
}

function setTheme(theme) {
  document.body.classList.remove('weather-sunny', 'weather-rainy', 'weather-cloudy', 'weather-snowy', 'weather-default');
  document.body.classList.add(`weather-${theme || 'default'}`);
}

function renderForecast(days) {
  forecastCards.innerHTML = days
    .map(
      (day) => `
        <article class="forecast-card reveal">
          <p class="forecast-day">${day.day}</p>
          <img class="forecast-icon" src="${day.icon}" alt="${day.condition} icon">
          <h4>${day.condition}</h4>
          <p class="forecast-description">${day.description}</p>
          <p class="forecast-range"><strong>${day.max_temp}°</strong> / ${day.min_temp}°</p>
        </article>
      `,
    )
    .join('');
}

function updateWeatherView(data) {
  clearError();
  setTheme(data.theme);

  cityName.textContent = data.city;
  weatherDescription.textContent = data.description;
  temperature.textContent = data.temperature;
  feelsLike.textContent = `${data.feels_like}°C`;
  humidity.textContent = `${data.humidity}%`;
  windSpeed.textContent = `${data.wind_speed} m/s`;
  weatherCondition.textContent = data.condition;
  localTime.textContent = data.local_time;

  if (data.icon) {
    weatherIcon.src = data.icon;
    weatherIcon.alt = `${data.description} icon`;
    weatherIcon.classList.add('is-visible');
    weatherIconAlt.classList.add('is-visible');
  }

  renderForecast(data.forecast);
}

async function fetchWeather(city) {
  const url = new URL(apiEndpoint, window.location.origin);
  url.searchParams.set('city', city);

  setLoading(true);
  try {
    const response = await fetch(url);
    const payload = await response.json();

    if (!response.ok || !payload.success) {
      throw new Error(payload.message || 'Unable to load weather data.');
    }

    updateWeatherView(payload.data);
    cityInput.value = city;
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
}

cityForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const city = cityInput.value.trim();

  if (!city) {
    showError('Please enter a city name to search.');
    return;
  }

  fetchWeather(city);
});

updateClock();
setInterval(updateClock, 1000);

const initialCity = new URLSearchParams(window.location.search).get('city');
if (initialCity) {
  cityInput.value = initialCity;
  fetchWeather(initialCity);
}
