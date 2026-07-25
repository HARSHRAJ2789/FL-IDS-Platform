import requests
import logging

class ThreatDetector:
    def __init__(self, model):
        self.model = model

    def analyze_flow(self, features_array):
        if len(features_array) == 0:
            return {"is_attack": False, "confidence": 0.0, "attack_indicators": []}

        # Predict
        preds = self.model.predict(features_array.reshape(1, -1))
        confidence = float(preds[0][0])
        is_attack = confidence > 0.5
        
        indicators = []
        if is_attack:
            if features_array[4] > 10000: # sbytes
                indicators.append("Large payload")
            if features_array[6] > 100: # rate
                indicators.append("High packet rate")
            if features_array[1] not in [6, 17]: # proto
                indicators.append("Uncommon protocol")
                
        return {
            "is_attack": is_attack,
            "confidence": confidence,
            "attack_indicators": indicators
        }

    def classify_attack_type(self, features):
        rate = features[6]
        smean = features[21]
        dpkts = features[3]
        sbytes = features[4]
        
        if rate > 1000 and smean < 100:
            return "DoS"
        elif dpkts == 0 and rate > 10:
            return "Probe"
        elif sbytes > 50000:
            return "Exploit"
        else:
            return "Generic"

    def get_severity(self, confidence):
        if confidence > 0.95:
            return "critical"
        elif confidence > 0.8:
            return "high"
        elif confidence > 0.65:
            return "medium"
        else:
            return "low"

    def report_to_server(self, alert_dict, server_url, api_key):
        try:
            headers = {"X-API-Key": api_key}
            response = requests.post(
                f"{server_url}/alerts",
                json=alert_dict,
                headers=headers,
                timeout=5
            )
            return response.status_code == 200 or response.status_code == 201
        except Exception as e:
            logging.error(f"Failed to report alert to server: {e}")
            return False
