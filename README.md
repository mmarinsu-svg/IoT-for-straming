# Sistema de Telemetría IoT y Detección de Anomalías en AWS

Este proyecto implementa una arquitectura Serverless en AWS para monitorear variables ambientales simuladas de 10 sensores en la Universidad Nacional (Sede Medellín).

## 🚀 Funcionalidades
- **Simulación IoT:** Sensores virtuales con física coherente (Temp/Humedad/Presión).
- **Comunicación:** MQTT seguro vía AWS IoT Core.
- **Procesamiento:** Detección de incendios en tiempo real con AWS Lambda.
- **Almacenamiento:** Arquitectura híbrida (DynamoDB + S3).
- **Visualización:** Tablero operativo en CloudWatch.
- **Analítica:** Consultas históricas con Amazon Athena.

## 🛠️ Tecnologías
- Python 3.9 (Boto3)
- AWS IoT Core, Lambda, DynamoDB, S3, SNS, Athena.

## ⚙️ Configuración e Instalación
1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Configurar credenciales de AWS en `~/.aws/credentials`.
4. Ejecutar el simulador: `python src/simulador_iot.py`

## 📸 Arquitectura
<img width="792" height="361" alt="Diagrama sin título drawio (1)" src="https://github.com/user-attachments/assets/89ebace3-9fc2-4fa9-b68f-9b7ed7031dbd" />

## 📋 Autor
Mateo Marin, Henry Cifuentes - Ingeniería Física - UNAL Medellín
