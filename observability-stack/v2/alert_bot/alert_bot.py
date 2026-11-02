from flask import Flask, request, jsonify
import docker
import logging
import time

app = Flask(__name__)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Docker client
try:
    docker_client = docker.from_env()
    logger.info("Docker client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Docker client: {e}")
    docker_client = None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive alerts from Alertmanager"""
    try:
        payload = request.json
        logger.info(f"Received webhook payload: {payload}")
        
        alerts = payload.get('alerts', [])
        
        for alert in alerts:
            alertname = alert['labels'].get('alertname', 'Unknown')
            status = alert.get('status', 'unknown')
            severity = alert['labels'].get('severity', 'info')
            
            logger.info(f"Processing alert: {alertname} | Status: {status} | Severity: {severity}")
            
            # Only handle firing critical/warning alerts
            if status == 'firing' and severity in ['critical', 'warning']:
                handle_alert(alertname, alert)
        
        return jsonify({"status": "ok", "processed": len(alerts)}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

def handle_alert(alertname, alert_data):
    """Handle specific alert types"""
    logger.info(f"Handling alert: {alertname}")
    
    if alertname == 'HighErrorRate':
        restart_container('flask_api')
    elif alertname == 'HighLatency':
        restart_container('flask_api')
    else:
        logger.info(f"No automated action defined for alert: {alertname}")

def restart_container(container_name):
    """Restart a Docker container"""
    if docker_client is None:
        logger.error("Docker client not initialized, cannot restart container")
        return
    
    try:
        container = docker_client.containers.get(container_name)
        logger.info(f"Restarting container: {container_name}")
        container.restart()
        logger.info(f"Successfully restarted container: {container_name}")
    except docker.errors.NotFound:
        logger.error(f"Container not found: {container_name}")
    except Exception as e:
        logger.error(f"Failed to restart container {container_name}: {e}")

if __name__ == '__main__':
    logger.info("Starting Alert Bot on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)