# CloudAPP

This repository contains the configuration for a Dockerized IoT architecture. It integrates multiple services to provide IoT management, data storage, and messaging capabilities:

- **Thingsboard**: IoT platform for device management, data collection, and visualization.
- **Minio**: S3-compatible object storage for saving and historizing IoT data.
- **Node-RED**: Flow-based programming tool to route IoT data to various endpoints.
- **RabbitMQ**: Messaging service for notifications and alerts.
- **Portainer**: Web UI for managing Docker containers and stacks.

---

## **Architecture Overview**

- IoT devices send telemetry data via MQTT to **Node-RED**.
- **Node-RED** routes data to:
  - **Thingsboard** for monitoring and visualization.
  - **Minio** for storage and historization.
  - **RabbitMQ** for push notifications and messaging.
- **Portainer** is used to manage all Docker containers running these services.

---

## **Installation Steps**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Aris9325/CloudAPP.git
   cd CloudAPP
