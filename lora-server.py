import paho.mqtt.client as mqtt
import json
import base64
import time
from datetime import datetime

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lorawan/uplink"
MQTT_AUTH_USER = "lorauser"
MQTT_AUTH_PASS = "lorapass"
APP_KEY = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"  # Doit correspondre à celui du nœud

# Classe IDS simplifié pour LoRaWAN
class LoRaWANIDS:
    def __init__(self):
        self.known_nodes = {}  # Stocke les informations sur les nœuds connus
        self.message_history = {}  # Pour la détection des attaques par rejeu
        self.alert_threshold = 3  # Nombre d'alertes avant notification
        self.alert_window = 300   # Fenêtre de temps pour les alertes (en secondes)
        self.authorized_gateways = {
            "farm_gateway_001": {
                "location": "Ferme principale",
                "last_seen": None,
                "status": "active"
            }
        }
        
    def is_gateway_authorized(self, gateway_id):
        """Vérifie si une passerelle est autorisée"""
        return gateway_id in self.authorized_gateways
        
    def register_gateway(self, gateway_id, location):
        """Enregistre une nouvelle passerelle autorisée"""
        if gateway_id not in self.authorized_gateways:
            self.authorized_gateways[gateway_id] = {
                "location": location,
                "last_seen": datetime.now().isoformat(),
                "status": "active"
            }
            print(f"Nouvelle passerelle enregistrée: {gateway_id} à {location}")
        
    def register_node(self, node_id):
        """Enregistre un nouveau nœud dans l'IDS"""
        if node_id not in self.known_nodes:
            self.known_nodes[node_id] = {
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'counters': {},
                'alerts': [],
                'rssi_history': []
            }
            print(f"Nouveau nœud enregistré: {node_id}")
    
    def analyze_message(self, message):
        """Analyse un message LoRaWAN pour détecter des anomalies"""
        try:
            # Extraction des informations pertinentes
            dev_id = message.get('dev_id')
            counter = message.get('counter')
            payload_raw = message.get('payload_raw')
            metadata = message.get('metadata', {})
            gateways = metadata.get('gateways', [])
            
            if not dev_id or counter is None or not payload_raw:
                return {'valid': False, 'reason': 'Message incomplet'}
                
            # Vérification des passerelles
            if not gateways:
                return {'valid': False, 'reason': 'Aucune passerelle dans les métadonnées'}
                
            for gateway in gateways:
                gateway_id = gateway.get('gtw_id')
                if not gateway_id:
                    continue
                    
                if not self.is_gateway_authorized(gateway_id):
                    anomalies.append({
                        'type': 'UNAUTHORIZED_GATEWAY',
                        'details': f'Passerelle non autorisée détectée: {gateway_id}'
                    })
                else:
                    # Mise à jour du statut de la passerelle
                    self.authorized_gateways[gateway_id]['last_seen'] = datetime.now().isoformat()
                    self.authorized_gateways[gateway_id]['status'] = 'active'
            
            # Vérifier si le nœud est connu
            if dev_id not in self.known_nodes:
                self.register_node(dev_id)
            
            # Mettre à jour les informations du nœud
            node_info = self.known_nodes[dev_id]
            node_info['last_seen'] = datetime.now().isoformat()
            
            # Vérification des anomalies
            anomalies = []
            
            # 1. Vérification du compteur (détection de rejeu)
            if dev_id in self.known_nodes and 'last_counter' in self.known_nodes[dev_id]['counters']:
                last_counter = self.known_nodes[dev_id]['counters']['last_counter']
                if counter <= last_counter:
                    anomalies.append({
                        'type': 'REPLAY_ATTACK',
                        'details': f'Compteur non incrémenté: actuel={counter}, précédent={last_counter}'
                    })
                elif counter > last_counter + 10:
                    anomalies.append({
                        'type': 'COUNTER_JUMP',
                        'details': f'Saut de compteur suspect: actuel={counter}, précédent={last_counter}'
                    })
            
            # Mise à jour du compteur
            self.known_nodes[dev_id]['counters']['last_counter'] = counter
            
            # 2. Vérification du MIC
            try:
                decoded = base64.b64decode(payload_raw)
                # Dans un scénario réel, nous vérifierions le MIC avec l'app_key
                # Simulation simplifiée ici
                valid_mic = True  # Supposons que c'est valide par défaut
                
                if not valid_mic:
                    anomalies.append({
                        'type': 'INVALID_MIC',
                        'details': 'Échec de la vérification du code d\'intégrité'
                    })
            except Exception as e:
                anomalies.append({
                    'type': 'PAYLOAD_ERROR',
                    'details': f'Erreur de décodage: {str(e)}'
                })
            
            # 3. Analyse RSSI pour détecter les usurpations potentielles
            if gateways:
                current_rssi = gateways[0].get('rssi', 0)
                self.known_nodes[dev_id]['rssi_history'].append(current_rssi)
                
                # Conserver uniquement les 10 dernières valeurs RSSI
                if len(self.known_nodes[dev_id]['rssi_history']) > 10:
                    self.known_nodes[dev_id]['rssi_history'] = self.known_nodes[dev_id]['rssi_history'][-10:]
                
                # Calculer la moyenne et l'écart-type des RSSI précédents
                if len(self.known_nodes[dev_id]['rssi_history']) >= 5:
                    avg_rssi = sum(self.known_nodes[dev_id]['rssi_history'][:-1]) / (len(self.known_nodes[dev_id]['rssi_history']) - 1)
                    
                    # Variation soudaine de RSSI (possible usurpation)
                    if abs(current_rssi - avg_rssi) > 20:  # Seuil arbitraire de 20 dBm
                        anomalies.append({
                            'type': 'RSSI_ANOMALY',
                            'details': f'Variation RSSI suspecte: actuel={current_rssi}, moyenne={avg_rssi:.2f}'
                        })
            
            # 4. Enregistrement des alertes si des anomalies sont détectées
            if anomalies:
                timestamp = datetime.now().isoformat()
                for anomaly in anomalies:
                    self.known_nodes[dev_id]['alerts'].append({
                        'timestamp': timestamp,
                        'type': anomaly['type'],
                        'details': anomaly['details']
                    })
                    print(f"ALERTE - Nœud {dev_id}: {anomaly['type']} - {anomaly['details']}")
                
                # Nettoyer les alertes trop anciennes
                current_time = time.time()
                self.known_nodes[dev_id]['alerts'] = [
                    alert for alert in self.known_nodes[dev_id]['alerts']
                    if (datetime.fromisoformat(alert['timestamp']).timestamp() + self.alert_window) > current_time
                ]
                
                # Vérifier le seuil d'alerte
                if len(self.known_nodes[dev_id]['alerts']) >= self.alert_threshold:
                    print(f"ALERTE CRITIQUE - Nœud {dev_id}: {self.alert_threshold} alertes en {self.alert_window} secondes")
                    # Ici, on pourrait déclencher une notification externe (email, SMS, etc.)
            
            return {
                'valid': len(anomalies) == 0,
                'anomalies': anomalies,
                'node_id': dev_id
            }
            
        except Exception as e:
            print(f"Erreur lors de l'analyse du message: {str(e)}")
            return {'valid': False, 'reason': f'Erreur d\'analyse: {str(e)}'}

# Gestionnaire de messages MQTT
class LoRaWANServer:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(MQTT_AUTH_USER, MQTT_AUTH_PASS)
        self.ids = LoRaWANIDS()
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connecté au broker MQTT avec code {rc}")
        client.subscribe(MQTT_TOPIC)
        print(f"Abonné au topic {MQTT_TOPIC}")
        
    def on_message(self, client, userdata, msg):
        print(f"Message reçu sur {msg.topic}")
        try:
            # Décodage du message JSON
            payload = json.loads(msg.payload.decode())
            
            # Analyse via l'IDS
            analysis = self.ids.analyze_message(payload)
            
            # Traitement des données en fonction de la validité
            if analysis.get('valid', False):
                self.process_valid_data(payload)
            else:
                print(f"Message invalide: {analysis.get('reason', 'Raison inconnue')}")
                if 'anomalies' in analysis and analysis['anomalies']:
                    for anomaly in analysis['anomalies']:
                        print(f"  - {anomaly['type']}: {anomaly['details']}")
                
        except json.JSONDecodeError:
            print("Erreur de décodage JSON")
        except Exception as e:
            print(f"Erreur de traitement du message: {str(e)}")
    
    def process_valid_data(self, message):
        """Traite les données valides des capteurs"""
        try:
            # Décodage du payload brut
            decoded = base64.b64decode(message['payload_raw'])
            
            # Dans un cas réel, nous déchiffrerions avec l'app_key
            # Ici on suppose que le format est JSON pour la simplicité
            # (ce ne serait pas le cas dans LoRaWAN réel qui utilise des formats binaires optimisés)
            data_part = decoded[:-4]  # Ignorer les 4 derniers octets (MIC simulé)
            
            try:
                sensor_data = json.loads(data_part.decode())
                print(f"Données de capteurs reçues du nœud {message['dev_id']}:")
                for reading in sensor_data:
                    print(f"  - {reading['type']}: {reading['value']} {reading['units']}")
                
                # Afficher les informations sur la passerelle
                if message.get('metadata', {}).get('gateways'):
                    gateway = message['metadata']['gateways'][0]
                    print(f"  Passerelle: {gateway.get('gtw_id')} (RSSI: {gateway.get('rssi')} dBm, SNR: {gateway.get('snr')} dB)")
            except:
                print("Format de données non-JSON, affichage brut:")
                print(f"  Données: {data_part}")
                
        except Exception as e:
            print(f"Erreur de traitement des données: {str(e)}")
    
    def start(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"Démarrage du serveur LoRaWAN sur {MQTT_BROKER}:{MQTT_PORT}")
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("Serveur arrêté par l'utilisateur")
        except Exception as e:
            print(f"Erreur de connexion: {str(e)}")
        finally:
            self.client.disconnect()
            print("Serveur arrêté")

# Point d'entrée principal
if __name__ == "__main__":
    server = LoRaWANServer()
    server.start()