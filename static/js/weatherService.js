// Weather API integration service
const OPENWEATHER_API_KEY = 'aecb2c3495db12bd54ea0e7aa6f8bce6'; // Free API key with limited requests

class WeatherService {
  /**
   * Fetches current weather data from OpenWeatherMap API
   * @param {number} lat - Latitude coordinate
   * @param {number} lon - Longitude coordinate
   * @returns {Promise} - Promise resolving to weather data
   */
  static async getCurrentWeather(lat, lon) {
    try {
      const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${OPENWEATHER_API_KEY}&units=metric`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching weather data:', error);
      return null;
    }
  }

  /**
   * Converts OpenWeatherMap data to application-friendly format
   * @param {Object} weatherData - Raw weather API response
   * @returns {Object} - Formatted weather data
   */
  static formatWeatherData(weatherData) {
    if (!weatherData) return null;
    
    return {
      temperature: weatherData.main.temp,
      humidity: weatherData.main.humidity,
      weatherMain: weatherData.weather[0].main,
      weatherDescription: weatherData.weather[0].description,
      weatherIcon: `https://openweathermap.org/img/wn/${weatherData.weather[0].icon}@2x.png`,
      windSpeed: weatherData.wind.speed,
      location: weatherData.name,
      country: weatherData.sys.country,
      pressure: weatherData.main.pressure,
      feels_like: weatherData.main.feels_like,
      timestamp: new Date(weatherData.dt * 1000).toLocaleString()
    };
  }

  /**
   * Estimates soil moisture based on recent weather conditions
   * @param {Object} weatherData - Weather data from API
   * @returns {number} - Estimated soil moisture percentage
   */
  static estimateSoilMoisture(weatherData) {
    if (!weatherData) return 0; // Default value if no data
    
    // Base moisture on current humidity and weather condition
    let baseMoisture = weatherData.main.humidity * 0.6;
    
    // Adjust based on weather condition
    const weatherMain = weatherData.weather[0].main.toLowerCase();
    
    if (weatherMain.includes('rain') || weatherMain.includes('shower')) {
      baseMoisture += 20;
    } else if (weatherMain.includes('drizzle')) {
      baseMoisture += 10;
    } else if (weatherMain.includes('clear') || weatherMain.includes('sun')) {
      baseMoisture -= 10;
    }
    
    // Ensure within 0-100 range
    return Math.min(Math.max(baseMoisture, 0), 80);
  }

  /**
   * Recommends soil type based on weather and location in Maharashtra
   * @param {Object} weatherData - Weather data from API
   * @param {string} region - Region in Maharashtra
   * @returns {string} - Recommended soil type
   */
  static recommendSoilType(weatherData, region) {
    if (!weatherData || !region) return "Black Soil"; // Default
    
    region = region.toLowerCase();
    
    // Region-based recommendations
    if (region.includes('vidarbha') || region.includes('marathwada')) {
      return "Black Soil";
    } else if (region.includes('western')) {
      return "Red Soil";
    } else if (region.includes('konkan')) {
      return "Laterite Soil";
    } else if (region.includes('north')) {
      return "Medium Black Soil";
    }
    
    // If no region match, recommend based on weather conditions
    const temp = weatherData.main.temp;
    const humidity = weatherData.main.humidity;
    
    if (temp > 30 && humidity < 50) {
      return "Black Soil"; // Hot and dry
    } else if (temp > 25 && humidity > 70) {
      return "Laterite Soil"; // Hot and humid
    } else {
      return "Medium Black Soil"; // Moderate conditions
    }
  }
}

export default WeatherService; 