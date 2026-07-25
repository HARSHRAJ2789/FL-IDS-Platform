import time
import threading
import socket
import requests
import logging
import json
import numpy as np
import signal
import sys
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from config import (
    SERVER_URL, API_KEY, INTERFACE, CAPTURE_DURATION, 
    LOCAL_EPOCHS, BATCH_SIZE, POLL_INTERVAL, MODEL_DIR, HOSTNAME
)
from feature_extractor import PacketFeatureExtractor
from trainer import LocalTrainer
from detector import ThreatDetector

# Setup rich logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()

class FLAgent:
    def __init__(self):
        self.running = True
        self.headers = {"X-API-Key": API_KEY}
        self.extractor = PacketFeatureExtractor(interface=INTERFACE)
        self.trainer = LocalTrainer()
        self.detector = ThreatDetector(self.trainer)
        self.ip_address = self._get_ip()
        
        # Load previous weights if available
        model_path = MODEL_DIR / "last_model.h5"
        if model_path.exists():
            self.trainer.load_model(model_path)
            logging.info("Loaded previous local model weights.")

    def _get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def register_client(self):
        try:
            payload = {
                "hostname": HOSTNAME,
                "ip": self.ip_address,
                "status": "online"
            }
            resp = requests.post(f"{SERVER_URL}/metrics/clients", json=payload, headers=self.headers, timeout=5)
            if resp.status_code in [200, 201]:
                logging.info(f"Registered client {HOSTNAME} ({self.ip_address}) with server.")
            else:
                logging.warning(f"Client registration returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logging.error(f"Failed to register client: {e}")

    def fetch_active_round(self):
        try:
            resp = requests.get(f"{SERVER_URL}/rounds/current", headers=self.headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
        except Exception as e:
            logging.error(f"Failed to fetch active round: {e}")
        return None

    def download_weights(self, round_id):
        try:
            resp = requests.get(f"{SERVER_URL}/rounds/{round_id}/weights", headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                weights_list = [np.array(w) for w in data.get('weights', [])]
                if weights_list:
                    self.trainer.set_weights(weights_list)
                    logging.info(f"Downloaded and applied weights for round {round_id}")
                    return True
        except Exception as e:
            logging.error(f"Failed to download weights: {e}")
        return False

    def submit_weights(self, round_id, weights, n_samples):
        try:
            weights_list = [w.tolist() for w in weights]
            payload = {
                "weights": weights_list,
                "n_samples": n_samples
            }
            resp = requests.post(
                f"{SERVER_URL}/rounds/{round_id}/submit",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            if resp.status_code in [200, 201]:
                logging.info(f"Successfully submitted weights for round {round_id}")
                return True
            else:
                logging.error(f"Failed to submit weights. Server returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logging.error(f"Error submitting weights: {e}")
        return False

    def fl_worker(self):
        logging.info("Started FL Worker Thread")
        while self.running:
            active_round = self.fetch_active_round()
            
            if active_round and active_round.get('status') == 'active':
                round_id = active_round.get('id')
                logging.info(f"Found active FL round: {round_id}")
                
                # 1. Download weights
                self.download_weights(round_id)
                
                # 2. Capture traffic for training
                logging.info(f"Capturing traffic for {CAPTURE_DURATION}s to train model...")
                df = self.extractor.capture_flows(CAPTURE_DURATION)
                n_samples = len(df)
                
                if n_samples > 0:
                    # In a real scenario, labels would be assigned.
                    # For this client, we simulate labels or pseudo-label using current model.
                    # As requested, label is 0 default, we can train on it (though conceptually weird, following prompt).
                    X = df.drop(columns=['label']).values
                    y = df['label'].values
                    
                    logging.info(f"Training on {n_samples} flow records...")
                    history = self.trainer.train(X, y, epochs=LOCAL_EPOCHS, batch_size=BATCH_SIZE)
                    
                    # 3. Submit weights
                    new_weights = self.trainer.get_weights()
                    self.submit_weights(round_id, new_weights, n_samples)
                    
                    # Save local
                    self.trainer.save_model(MODEL_DIR / "last_model.h5")
                else:
                    logging.info("No traffic captured. Skipping training this round.")
            else:
                logging.debug("No active round found. Sleeping...")
                
            # Sleep until next poll interval
            for _ in range(POLL_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def detection_worker(self):
        logging.info("Started Detection Worker Thread")
        while self.running:
            # Continuous packet capture in short bursts for real-time detection
            df = self.extractor.capture_flows(10)
            if len(df) > 0:
                X = df.drop(columns=['label']).values
                for i in range(len(X)):
                    flow_features = X[i]
                    alert_info = self.detector.analyze_flow(flow_features)
                    
                    if alert_info['is_attack']:
                        attack_type = self.detector.classify_attack_type(flow_features)
                        severity = self.detector.get_severity(alert_info['confidence'])
                        
                        alert_payload = {
                            "client_id": HOSTNAME,
                            "attack_type": attack_type,
                            "severity": severity,
                            "confidence": alert_info['confidence'],
                            "indicators": alert_info['attack_indicators'],
                            "timestamp": time.time()
                        }
                        
                        logging.warning(f"Threat Detected! Type: {attack_type}, Severity: {severity}")
                        self.detector.report_to_server(alert_payload, SERVER_URL, API_KEY)
            
            if not self.running:
                break

    def display_status(self):
        while self.running:
            table = Table(title="FL-IDS Agent Status")
            table.add_column("Property", justify="right", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")
            
            table.add_row("Hostname", HOSTNAME)
            table.add_row("IP", self.ip_address)
            table.add_row("Server URL", SERVER_URL)
            table.add_row("Interface", str(INTERFACE))
            table.add_row("Status", "Running")
            
            console.print(table)
            
            for _ in range(30):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        logging.info(f"Starting FL-IDS Agent on {HOSTNAME}")
        self.register_client()
        
        t_fl = threading.Thread(target=self.fl_worker, daemon=True)
        t_detect = threading.Thread(target=self.detection_worker, daemon=True)
        t_status = threading.Thread(target=self.display_status, daemon=True)
        
        t_fl.start()
        t_detect.start()
        t_status.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logging.info("Shutting down agent...")
        self.running = False
        sys.exit(0)

if __name__ == "__main__":
    agent = FLAgent()
    agent.start()
