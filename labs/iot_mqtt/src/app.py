import os
import time
import random
import json
import threading
import logging
from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

BROKER = "127.0.0.1"
PORT = 1883
FLAG = os.environ.get("IOT_FLAG", "FLAG{TEST_FLAG_123}")
DOOR_PIN = os.environ.get("DOOR_PIN", "123456")

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/unlock", methods=["POST"])
def unlock():
    data = request.json
    if not data or "pin" not in data:
        return jsonify({"success": False, "message": "No PIN provided"}), 400
    
    if data["pin"] == DOOR_PIN:
        logging.info("Valid PIN received via Web UI. Revealing flag.")
        return jsonify({"success": True, "flag": FLAG})
    else:
        logging.warning("Invalid PIN attempt.")
        return jsonify({"success": False, "message": "Invalid PIN"})


# MQTT Background Worker
def mqtt_worker():
    client = mqtt.Client(client_id="SmartHomeHub")
    
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception as e:
            logging.error(f"Waiting for MQTT Broker... {e}")
            time.sleep(2)

    client.loop_start()
    logging.info("MQTT Client connected and loop started.")

    counter = 0
    while True:
        time.sleep(5)
        
        # Publish living room temperature
        temp = round(random.uniform(22.0, 26.5), 1)
        client.publish("home/livingroom/temp", f"{temp}°C")
        
        # Publish door status
        if counter % 4 == 0:
            client.publish("home/frontdoor/status", "LOCKED")
        
        # Leak the PIN (Notice it's leaking DOOR_PIN, not FLAG)
        if counter % 3 == 0:
            leak_data = {
                "device": "smart_bulb_controller",
                "auth_pin": DOOR_PIN,
                "status": "ready"
            }
            client.publish("home/security/door_pin", json.dumps(leak_data))
            
        counter += 1

if __name__ == "__main__":
    # Start MQTT worker
    threading.Thread(target=mqtt_worker, daemon=True).start()
    # Start Flask Web App
    app.run(host="0.0.0.0", port=80, debug=False)
