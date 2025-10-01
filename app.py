import os
import subprocess
import sys
import time
import threading
import webbrowser
import pickle
import pandas as pd
import json
import re
from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from transformers import pipeline
from PIL import Image
import torch
from datetime import datetime
import requests

app = Flask(__name__)

# --- Global Configurations ---
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Leaf Disease Detection Model Initialization ---
pipe = pipeline("image-classification", 
                model="linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# --- Seed Size Analysis Model Initialization ---
# Get the directory of the current app.py file
current_app_dir = os.path.dirname(os.path.abspath(__file__))

def get_absolute_path(relative_path):
    # Now that the .pkl files are in the root, we don't need 'seedSize/' prefix
    return os.path.join(current_app_dir, relative_path)

# Load the machine learning models and encoders
try:
    with open(get_absolute_path('agricultural_models.pkl'), 'rb') as f:
        models = pickle.load(f)
    seed_size_model = models['seed_size_model']
    sowing_depth_model = models['sowing_depth_model']
    spacing_model = models['spacing_model']
    label_encoders = models['label_encoders']
except FileNotFoundError:
    print("Error: agricultural_models.pkl not found. Make sure agricultural_models.pkl exists in the root directory.")
    # Handle error appropriately, e.g., set models to None and return an error on routes
    seed_size_model = None
    sowing_depth_model = None
    spacing_model = None
    label_encoders = {}

# Load unique dropdown values for crop name, region, etc.
try:
    with open(get_absolute_path('unique_values.pkl'), 'rb') as f:
        unique_values = pickle.load(f)
    # The dropdown values for soil type are still taken from here
    # The detailed soil_types list will be hardcoded below for consistency
except FileNotFoundError:
    print("Error: unique_values.pkl not found. Make sure unique_values.pkl exists in the root directory.")
    unique_values = {'Crop Name': [], 'Region': [], 'Season': [], 'Soil Type': []}

# Detailed soil types data (moved from seedSize/app.py and hardcoded for consistency)
soil_types_data = [
    {
        "id": "black_soil",
        "name": "Black Soil",
        "description": "Black soil, or Regur soil, is rich in clay minerals, calcium carbonate, magnesium, potash, and lime. It has excellent water retention capacity and is highly suitable for cotton cultivation.",
        "color": "#2d2d2d",
        "characteristics": [
            "High water retention",
            "Rich in nutrients",
            "Clay-like texture",
            "Self-ploughing nature"
        ],
        "suitable_crops": [],
        "regions": ["Vidarbha", "Marathwada"]
    },
    {
        "id": "red_soil",
        "name": "Red Soil",
        "description": "Red soil gets its color from iron oxide. It is generally poor in nitrogen, phosphoric acid, and organic matter but rich in potash. It's porous with good drainage properties.",
        "color": "#8B2500",
        "characteristics": [
            "Porous and well-drained",
            "Rich in iron oxides",
            "Poor in nitrogen",
            "Sandy to clayey texture"
        ],
        "suitable_crops": [],
        "regions": ["Western Maharashtra"]
    },
    {
        "id": "laterite_soil",
        "name": "Laterite Soil",
        "description": "Laterite soil is formed under tropical conditions due to intense weathering. It's rich in iron and aluminum but poor in nitrogen, potash, potassium, lime, and magnesium.",
        "color": "#BA8759",
        "characteristics": [
            "Highly weathered",
            "Rich in iron and aluminum",
            "Poor in organic matter",
            "Acidic nature"
        ],
        "suitable_crops": [],
        "regions": ["Konkan"]
    },
    {
        "id": "medium_black_soil",
        "name": "Medium Black Soil",
        "description": "Medium black soil is less clayey than pure black soil but still has good moisture retention and nutrient content. It's versatile and supports a wide range of crops.",
        "color": "#4A4A4A",
        "characteristics": [
            "Moderate water retention",
            "Well-balanced texture",
            "Good fertility",
            "Mixed clayey and loamy"
        ],
        "suitable_crops": [],
        "regions": ["North Maharashtra"]
    },
    {
        "id": "alluvial_soil",
        "name": "Alluvial Soil",
        "description": "Alluvial soil is formed by sediment deposited by rivers. It's extremely fertile with high amounts of potash, phosphoric acid, and lime but varying proportions of organic matter.",
        "color": "#D3C1AD",
        "characteristics": [
            "Very fertile",
            "Rich in minerals",
            "Variable texture",
            "Renewable fertility"
        ],
        "suitable_crops": [],
        "regions": ["Various river basins in Maharashtra"]
    },
    {
        "id": "sandy_soil",
        "name": "Sandy Soil",
        "description": "Sandy soil has large particles with excellent drainage but poor water and nutrient retention. It warms quickly in spring and is typically acidic. Suitable for early planting, root vegetables, and drought-resistant plants.",
        "color": "#E6CC8A",
        "characteristics": [
            "Excellent drainage",
            "Poor water retention",
            "Low nutrient content",
            "Warms quickly"
        ],
        "suitable_crops": [],
        "regions": ["Arid and semi-arid areas, river banks"]
    }
]

# --- Helper Functions (from run.py) ---
def clear_screen():
    """Clear the terminal screen based on the OS"""
    if os.name == 'nt':  # For Windows
        os.system('cls')
    else:  # For Unix/Linux/Mac
        os.system('clear')

def print_banner():
    """Print application banner"""
    banner = """
    ===============================================
      Agricultural Analysis Suite - Launch Tool
    ===============================================
    """
    print(banner)

def wait_for_exit():
    """Wait for the process to exit"""
    try:
        print("\nPress Ctrl+C to stop all applications")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down applications...")

def check_requirements():
    """Check and install requirements if needed"""
    try:
        import flask # Check for Flask explicitly
        print("Flask is already installed.")
    except ImportError:
        print("Flask is not installed. Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Packages installed successfully.")

# --- Helper Functions (from seedSize/app.py) ---
def get_soil_info(soil_type):
    """Get soil type specific information with detailed descriptions"""
    for soil in soil_types_data: # Use the hardcoded list here
        if soil['name'].lower() == soil_type.lower():
            return soil['description']
    # Fallback to the hardcoded dictionary if not found in soil_types_data list
    soil_info_fallback = {
        'Black Soil': 'Black soil, or Regur soil, is rich in clay minerals, calcium carbonate, magnesium, potash, and lime. It has excellent water retention capacity with high clay content (alkaline with pH 7.5-8.5). Ideal for cotton cultivation and self-ploughing in nature.',
        'Red Soil': 'Red soil gets its color from iron oxide. It is generally poor in nitrogen, phosphoric acid, and organic matter but rich in potash. It has porous structure with good drainage properties, slightly acidic with pH 6.0-6.8, suitable for millets and legumes.',
        'Laterite Soil': 'Laterite soil is formed under tropical conditions due to intense weathering. It\'s rich in iron and aluminum oxides but poor in nitrogen, potash, calcium, lime, and magnesium. Highly acidic with pH 5.0-6.0, requires fertilization, suitable for plantation crops.',
        'Medium Black Soil': 'Medium black soil is less clayey than pure black soil but still has good moisture retention and nutrient content. It has balanced drainage and water retention with pH 7.0-8.0. Versatile and supports a wide range of crops with good fertility.',
        'Alluvial Soil': 'Alluvial soil is formed by sediment deposited by rivers. It\'s extremely fertile with high amounts of potash, phosphoric acid, and lime but varying proportions of organic matter. Has variable texture with pH 6.5-7.5, excellent for intensive agriculture.',
        'Sandy Soil': 'Sandy soil has large particles with excellent drainage but poor water and nutrient retention. It\'s typically acidic with pH 5.5-6.5 and warms quickly in spring. Suitable for early planting, root vegetables, and drought-resistant plants.'
    }
    for key, description in soil_info_fallback.items():
        if key.lower() == soil_type.lower():
            return description
    for key, description in soil_info_fallback.items():
        if key.lower() in soil_type.lower() or soil_type.lower() in key.lower():
            return description
    soil_keywords = ['black', 'red', 'laterite', 'alluvial', 'sandy', 'medium']
    soil_type_lower = soil_type.lower()
    for keyword in soil_keywords:
        if keyword in soil_type_lower:
            for key, description in soil_info_fallback.items():
                if keyword in key.lower():
                    return description
    return f"{soil_type} is found across various regions of Maharashtra. It has distinctive properties that influence crop selection and agricultural practices based on its texture, drainage characteristics, and mineral composition."

def get_region_info(region):
    """Get region specific information"""
    region_info = {
        'Vidarbha': 'hot and dry climate, moderate rainfall of 700-900mm annually',
        'Marathwada': 'semi-arid climate, low rainfall (600-800mm), prone to drought',
        'Western Maharashtra': 'moderate rainfall (700-1200mm), diverse climate zones',
        'Konkan': 'high rainfall region (2500-3500mm), coastal climate, humid',
        'North Maharashtra': 'varied climate with moderate rainfall (600-900mm)'
    }
    return region_info.get(region, 'specific regional climate and growing conditions')

def get_season_info(season):
    """Get seasonal information"""
    season_info = {
        'Kharif': 'monsoon season from June to October, warm and humid with plenty of rainfall',
        'Rabi': 'winter season from October to March, cooler temperatures with limited rainfall',
        'Summer': 'hot dry season from March to June, high temperatures with very limited rainfall'
    }
    return season_info.get(season, 'specific growing season with characteristic climate')

def is_default_set(crops):
    """Check if the crop list matches the common default set"""
    default_crops = set(['wheat', 'rice', 'cotton', 'jowar', 'bajra'])
    found_crops = set([c.lower() for c in crops])
    return len(found_crops.intersection(default_crops)) >= 3

def get_fallback_crops(soil_type, region, season, temperature, moisture):
    """Get fallback crops based on soil type, region, and season"""
    temp_range = 'Normal'
    if temperature < 20:
        temp_range = 'Cool'
    elif temperature > 30:
        temp_range = 'Hot'
    moisture_range = 'Medium'
    if moisture < 40:
        moisture_range = 'Dry'
    elif moisture > 70:
        moisture_range = 'Wet'
    key = f"{soil_type}_{region}_{season}_{temp_range}_{moisture_range}".replace(' ', '')
    fallbacks = {
        'BlackSoil_Vidarbha_Kharif_Hot_Dry': ['Cotton', 'Moth Bean', 'Cluster Bean', 'Castor', 'Sesame'],
        'BlackSoil_Vidarbha_Rabi_Cool_Medium': ['Wheat', 'Chickpea', 'Safflower', 'Linseed', 'Coriander'],
        'BlackSoil_Vidarbha_Summer_Hot_Dry': ['Sunflower', 'Mung Bean', 'Cluster Bean', 'Watermelon', 'Bitter Gourd'],
        'RedSoil_WesternMaharashtra_Kharif_Hot_Dry': ['Pearl Millet', 'Moth Bean', 'Cluster Bean', 'Horse Gram', 'Castor'],
        'RedSoil_WesternMaharashtra_Rabi_Cool_Medium': ['Chickpea', 'Safflower', 'Fenugreek', 'Coriander', 'Mustard'],
        'RedSoil_WesternMaharashtra_Summer_Hot_Medium': ['Groundnut', 'Sesame', 'Okra', 'Bitter Gourd', 'Ridge Gourd'],
        'LateriteSoil_Konkan_Kharif_Hot_Wet': ['Rice', 'Finger Millet', 'Black Gram', 'Cowpea', 'Bitter Gourd'],
        'LateriteSoil_Konkan_Rabi_Cool_Medium': ['Sweet Potato', 'Colocasia', 'Turmeric', 'Elephant Foot Yam', 'Pulses'],
        'LateriteSoil_Konkan_Summer_Hot_Wet': ['Snake Gourd', 'Ridge Gourd', 'Bitter Gourd', 'Cucumber', 'Chillies'],
        'AlluvialSoil_WesternMaharashtra_Kharif_Hot_Wet': ['Rice', 'Taro', 'Water Chestnut', 'Lotus Root', 'Turmeric'],
        'AlluvialSoil_WesternMaharashtra_Rabi_Cool_Medium': ['Potato', 'Onion', 'Garlic', 'Tomato', 'Spinach'],
        'AlluvialSoil_WesternMaharashtra_Summer_Hot_Medium': ['Muskmelon', 'Bitter Gourd', 'Okra', 'Snake Gourd', 'Cucumber']
    }
    if key in fallbacks:
        return fallbacks[key]
    key_simple = f"{soil_type}_{season}".replace(' ', '')
    simple_fallbacks = {
        'BlackSoil_Kharif': ['Cotton', 'Soybean', 'Pigeon Pea', 'Green Gram', 'Sorghum'],
        'BlackSoil_Rabi': ['Wheat', 'Chickpea', 'Safflower', 'Linseed', 'Mustard'],
        'BlackSoil_Summer': ['Sunflower', 'Sesame', 'Green Gram', 'Groundnut', 'Bottle Gourd'],
        'RedSoil_Kharif': ['Pearl Millet', 'Groundnut', 'Pigeon Pea', 'Green Gram', 'Sorghum'],
        'RedSoil_Rabi': ['Sorghum', 'Chickpea', 'Safflower', 'Sunflower', 'Mustard'],
        'RedSoil_Summer': ['Groundnut', 'Sesame', 'Bitter Gourd', 'Watermelon', 'Muskmelon'],
        'LateriteSoil_Kharif': ['Rice', 'Finger Millet', 'Cowpea', 'Horse Gram', 'Sesame'],
        'LateriteSoil_Rabi': ['Finger Millet', 'Sweet Potato', 'Pulses', 'Turmeric', 'Elephant Foot Yam'],
        'LateriteSoil_Summer': ['Bitter Gourd', 'Ridge Gourd', 'Cucumber', 'Snake Gourd', 'Chillies'],
        'MediumBlackSoil_Kharif': ['Cotton', 'Pearl Millet', 'Sorghum', 'Pigeon Pea', 'Green Gram'],
        'MediumBlackSoil_Rabi': ['Wheat', 'Chickpea', 'Safflower', 'Mustard', 'Fenugreek'],
        'MediumBlackSoil_Summer': ['Groundnut', 'Sunflower', 'Bitter Gourd', 'Ridge Gourd', 'Watermelon'],
        'AlluvialSoil_Kharif': ['Rice', 'Sugarcane', 'Turmeric', 'Ginger', 'Taro'],
        'AlluvialSoil_Rabi': ['Wheat', 'Potato', 'Onion', 'Garlic', 'Tomato'],
        'AlluvialSoil_Summer': ['Muskmelon', 'Watermelon', 'Cucumber', 'Bitter Gourd', 'Okra'],
        'SandySoil_Kharif': ['Pearl Millet', 'Cluster Bean', 'Moth Bean', 'Sesame', 'Cowpea'],
        'SandySoil_Rabi': ['Cumin', 'Mustard', 'Chickpea', 'Coriander', 'Fenugreek'],
        'SandySoil_Summer': ['Watermelon', 'Muskmelon', 'Cluster Bean', 'Cucumber', 'Ridge Gourd']
    }
    if key_simple in simple_fallbacks:
        return simple_fallbacks[key_simple]
    soil_fallbacks = {
        'Black Soil': ['Soybean', 'Pigeon Pea', 'Sunflower', 'Safflower', 'Chickpea'],
        'Red Soil': ['Pearl Millet', 'Groundnut', 'Pigeon Pea', 'Sesame', 'Mustard'],
        'Laterite Soil': ['Finger Millet', 'Sweet Potato', 'Turmeric', 'Bitter Gourd', 'Snake Gourd'],
        'Medium Black Soil': ['Soybean', 'Chickpea', 'Sunflower', 'Mustard', 'Pigeon Pea'],
        'Alluvial Soil': ['Potato', 'Sugarcane', 'Onion', 'Turmeric', 'Ginger'],
        'Sandy Soil': ['Watermelon', 'Muskmelon', 'Cluster Bean', 'Groundnut', 'Sesame']
    }
    if soil_type in soil_fallbacks:
        return soil_fallbacks[soil_type]
    return ['Sunflower', 'Green Gram', 'Groundnut', 'Okra', 'Bitter Gourd']

# --- Routes ---
@app.route('/')
def home():
    """Render the homepage"""
    return render_template('homepage.html')

@app.route('/leaf_disease')
def leaf_index():
    """Render the leaf disease detection page"""
    return render_template('leaf_disease_index.html')

@app.route('/sensor_docs')
def sensor_docs():
    """Render the sensor documentation page"""
    return render_template('sensor_docs.html')

@app.route('/leaf_disease/predict', methods=['POST'])
def leaf_predict():
    """Handle leaf disease prediction"""
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            image = Image.open(filepath)
            predictions = pipe(image)
            
            formatted_predictions = [
                {
                    'disease': pred['label'],
                    'confidence': f"{pred['score']*100:.2f}%",
                    'score': pred['score']
                }
                for pred in predictions
            ]
            
            return jsonify({
                'success': True,
                'predictions': formatted_predictions,
                'top_prediction': formatted_predictions[0],
                'image_path': f'/static/uploads/{filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/seed_size')
def seed_index():
    """Render the seed size analysis page"""
    return render_template('seed_size_index.html',
                           crops=unique_values['Crop Name'],
                           regions=unique_values['Region'],
                           seasons=unique_values['Season'],
                           soil_types=unique_values['Soil Type'], # Still pass the list of strings for dropdown
                           soil_data=soil_types_data) # Pass the detailed soil data for JS logic

@app.route('/seed_size/predict', methods=['POST'])
def seed_predict():
    """Handle seed size prediction"""
    if seed_size_model is None or sowing_depth_model is None or spacing_model is None:
        return jsonify({'error': 'ML models not loaded, check server logs.'}), 500

    try:
        crop_name = request.form['crop_name']
        region = request.form['region']
        season = request.form['season']
        temperature = float(request.form.get('temperature', 0))
        moisture = float(request.form.get('moisture', 0))
        soil_type = request.form['soil_type']
        soil_ph = float(request.form['soil_ph'])

        crop_name_encoded = label_encoders['Crop Name'].transform([crop_name])[0]
        region_encoded = label_encoders['Region'].transform([region])[0]
        season_encoded = label_encoders['Season'].transform([season])[0]
        soil_type_encoded = label_encoders['Soil Type'].transform([soil_type])[0]

        input_features = [[crop_name_encoded, region_encoded, season_encoded,
                           temperature, moisture, soil_type_encoded, soil_ph]]

        print(f"Input features for prediction: {input_features}") # Debug print

        seed_size_encoded = seed_size_model.predict(input_features)[0]
        sowing_depth = sowing_depth_model.predict(input_features)[0]
        spacing = spacing_model.predict(input_features)[0]

        seed_size = label_encoders['Seed Size Category'].inverse_transform([seed_size_encoded])[0]

        sowing_depth = round(sowing_depth, 2)
        spacing = round(spacing, 2)

        soil_data = {}
        for soil in soil_types_data: # Use the detailed data here
            if soil['name'] == soil_type:
                soil_data = soil
                break
        if not soil_data:
            soil_description = get_soil_info(soil_type)
            soil_data = {'name': soil_type, 'description': soil_description, 'suitable_crops': []}

        # Get crop recommendations directly using fallback logic
        recommended_crops_list = get_fallback_crops(soil_type, region, season, temperature, moisture)

        print(f"Prediction results: Seed Size: {seed_size}, Sowing Depth: {sowing_depth}, Spacing: {spacing}, Recommended Crops: {recommended_crops_list}") # Debug print

        return jsonify({
            'seed_size': seed_size,
            'sowing_depth': sowing_depth,
            'spacing': spacing,
            'selected_soil_type': soil_type,
            'soil_description': soil_data.get('description', ''),
            'recommended_crops': recommended_crops_list # Directly return the fallback crops
        })

    except Exception as e:
        app.logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/soil-types', methods=['GET'])
def get_soil_types_api(): # Renamed to avoid conflict with global variable
    """Returns all soil type details as JSON"""
    return jsonify(soil_types_data) # Return the detailed soil data

@app.route('/api/weather-proxy', methods=['GET'])
def weather_proxy():
    """API proxy for Open-Meteo with error handling"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')

        if not lat or not lon:
            return jsonify({'error': 'Latitude and longitude are required.'}), 400

        # Open-Meteo API endpoint (no API key required for basic usage)
        open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&forecast_days=1"
        response = requests.get(open_meteo_url, timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if 'current_weather' in data and data['current_weather']:
            current_weather = data['current_weather']
            # Open-Meteo provides 'temperature', 'windspeed', 'winddirection', 'weathercode', 'is_day'
            # We need to map weathercode to a 'description' or 'main' for frontend compatibility
            # For simplicity, we'll just return the raw values and let the frontend adapt
            return jsonify({
                'temperature': current_weather.get('temperature'),
                'humidity': None, # Open-Meteo current_weather does not provide humidity directly in this endpoint
                'weathercode': current_weather.get('weathercode'),
                'windspeed': current_weather.get('windspeed'),
                'is_day': current_weather.get('is_day'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timezone': data.get('timezone')
            })
        else:
            app.logger.warning(f"Open-Meteo API did not return current_weather data for lat={lat}, lon={lon}. Response: {data}")
            return jsonify({'error': 'Could not retrieve current weather data. Please try again later.'}), 500

    except requests.exceptions.Timeout:
        app.logger.error(f"Open-Meteo API request timed out for lat={lat}, lon={lon}.")
        return jsonify({'error': 'Weather service timed out. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching weather data from Open-Meteo for lat={lat}, lon={lon}: {e}")
        return jsonify({'error': f'Weather service error: {e}. Please try again.'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in weather_proxy: {e}")
        return jsonify({'error': 'An unexpected error occurred with the weather service.'}), 500

@app.route('/sensorData/plant_data.json')
def get_sensor_data():
    """API endpoint to serve the sensor data from the sensorData folder"""
    try:
        sensor_data_path = get_absolute_path(os.path.join('seedSize', 'sensorData', 'plant_data.json'))
        if not os.path.exists(sensor_data_path):
            dummy_data = [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": 0,"humidity": 0,"soil_moisture": 0,
                "motion_detected": "NO","pump_state": "OFF"}
            ]
            return jsonify(dummy_data)
        with open(sensor_data_path, 'r') as file:
            sensor_data = file.read()
        return app.response_class(response=sensor_data, status=200, mimetype='application/json')
    except Exception as e:
        app.logger.error(f"Sensor data error: {str(e)}")
        return jsonify([{"error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         "temperature": 0,"humidity": 0,"soil_moisture": 0,
                         "motion_detected": "ERROR","pump_state": "ERROR"}]), 500

@app.route('/api/update-sensor-data', methods=['POST'])
def update_sensor_data():
    """API endpoint to execute plant_monitor.py and update sensor data"""
    try:
        plant_monitor_path = get_absolute_path(os.path.join('seedSize', 'sensorData', 'plant_monitor.py'))
        result = subprocess.run([sys.executable, plant_monitor_path], 
                               capture_output=True, text=True,
                               cwd=get_absolute_path(os.path.join('seedSize', 'sensorData')))
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "Sensor data updated"})
        else:
            return jsonify({"status": "error", "message": "Failed to update sensor data","error": result.stderr}), 500
    except Exception as e:
        app.logger.error(f"Update sensor data error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Application Run ---
if __name__ == '__main__':
    clear_screen()
    print_banner()
    
    # Check requirements
    check_requirements()

    # Open browser in a separate thread
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open(os.environ.get('APP_URL', 'http://localhost:8000')))).start()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 8000))
    # In a production environment, you might use gunicorn:
    # command = f"gunicorn --bind 0.0.0.0:{port} app:app"
    # subprocess.Popen(command.split())
    app.run(host='0.0.0.0', port=port, debug=False)

    # Wait for exit after the Flask app is running
    wait_for_exit()

    print("Application shutdown complete.") 
