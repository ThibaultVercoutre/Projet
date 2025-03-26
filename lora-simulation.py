import time
import json
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import hashlib
import hmac
import base64

# Configuration
NODE_ID = "agriculture_node_001"
GATEWAY_ID = "farm_gateway_001"
APP_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"  # Clé de sécurité (simulée)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lorawan/uplink"
MQTT_AUTH_USER = "lorauser"
MQTT_AUTH_PASS = "lorapass"

# Simulation des capteurs
class VirtualSensor:
    def __init__(self, sensor_id, sensor_type, min_val, max_val, units):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.min_val = min_val
        self.max_val = max_val
        self.units = units
        self.last_value = None
        
    def read(self):
        # Simulation d'une lecture de capteur avec un peu de réalisme
        if self.last_value is None:
            # Première lecture
            self.last_value = random.uniform(self.min_val, self.max_val)
        else:
            # Les lectures suivantes varient légèrement par rapport à la dernière
            variation = random.uniform(-0.1, 0.1) * (self.max_val - self.min_val)
            new_value = self.last_value + variation
            # Assurer que la valeur reste dans les limites
            self.last_value = max(self.min_val, min(self.max_val, new_value))
            
        return {
            "sensor_id": self.sensor_id,
            "type": self.sensor_type,
            "value": round(self.last_value, 2),
            "units": self.units,
            "timestamp": datetime.now().isoformat()
        }

# Définition des capteurs virtuels
sensors = [
    VirtualSensor("temp_001", "temperature", 10, 40, "°C"),
    VirtualSensor("humidity_001", "soil_moisture", 20, 80, "%"),
    VirtualSensor("light_001", "light_intensity", 0, 1000, "lux"),
    VirtualSensor("pest_001", "pest_detection", 0, 10, "count")
]

# Simulation de la couche LoRaWAN
class LoRaWANSimulator:
    def __init__(self, node_id, app_key):
        self.node_id = node_id
        self.app_key = app_key
        self.frame_counter = 0
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(MQTT_AUTH_USER, MQTT_AUTH_PASS)
        
    def connect(self):
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"Connecté au broker MQTT {MQTT_BROKER}:{MQTT_PORT}")
            return True
        except Exception as e:
            print(f"Erreur de connexion au broker MQTT: {e}")
            return False
            
    def create_payload(self, sensor_data):
        # Création d'un payload similaire à LoRaWAN
        payload = {
            "dev_id": self.node_id,
            "counter": self.frame_counter,
            "port": 1,
            "payload_raw": self._encode_sensor_data(sensor_data),
            "metadata": {
                "time": datetime.now().isoformat(),
                "frequency": 868.1,
                "modulation": "LORA",
                "data_rate": "SF7BW125",
                "coding_rate": "4/5",
                "gateways": [{
                    "gtw_id": GATEWAY_ID,
                    "rssi": -100,
                    "snr": 10
                }]
            }
        }
        return payload
        
    def _encode_sensor_data(self, sensor_data):
        # Simulation du chiffrement et de l'encodage des données capteur
        # Dans LoRaWAN réel, ceci utiliserait AES-128 avec l'app_key
        data_str = json.dumps(sensor_data)
        
        # Création d'un MIC (Message Integrity Code) simulé
        key = bytes.fromhex(self.app_key)
        h = hmac.new(key, data_str.encode(), hashlib.sha256)
        mic = h.digest()[:4]  # 4 octets pour le MIC
        
        # Encodage en base64 (simulant le payload LoRaWAN)
        combined = data_str.encode() + mic
        return base64.b64encode(combined).decode()
        
    def send_data(self, sensor_data):
        payload = self.create_payload(sensor_data)
        
        # Simulation d'une transmission LoRaWAN
        print(f"Envoi de données LoRaWAN (frame #{self.frame_counter}):")
        print(f"  Capteurs: {len(sensor_data)} lectures")
        
        # Publication sur MQTT (simulant la passerelle LoRaWAN)
        self.mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
        print(f"  Données publiées sur {MQTT_TOPIC}")
        
        self.frame_counter += 1
        return True

# Programme principal
def main():
    print(f"Démarrage de la simulation du nœud LoRa {NODE_ID}")
    
    # Initialisation du simulateur LoRaWAN
    lora_sim = LoRaWANSimulator(NODE_ID, APP_KEY)
    
    if not lora_sim.connect():
        print("Impossible de se connecter au broker MQTT. Fin du programme.")
        return
    
    try:
        while True:
            # Collecte des données des capteurs
            sensor_readings = [sensor.read() for sensor in sensors]
            print(f"Lecture des capteurs: {len(sensor_readings)} valeurs")
            
            # Envoi des données via LoRaWAN simulé
            lora_sim.send_data(sensor_readings)
            
            # Attente avant la prochaine transmission
            # Les nœuds LoRa transmettent généralement à des intervalles de plusieurs minutes
            # pour économiser la batterie
            wait_time = random.randint(5, 15)  # En secondes pour la simulation (serait plus long en réalité)
            print(f"Attente de {wait_time} secondes avant la prochaine transmission...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("Simulation interrompue par l'utilisateur")
    finally:
        print("Fin de la simulation")

if __name__ == "__main__":
    main()