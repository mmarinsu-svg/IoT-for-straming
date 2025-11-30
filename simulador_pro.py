import boto3
import json
import time
import random
import logging
from datetime import datetime

# --- CONFIGURACIÓN ---
REGION = "us-east-1"
TOPIC = "iot/sensor/data"
BATCH_SIZE = 5  # Enviar cada 5 mediciones (Cumple desafío de Batching)

# Configuración de Logging (Para ver errores como un pro)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class SensorIoT:
    def __init__(self, device_id, lat, lon):
        self.device_id = device_id
        self.client = boto3.client('iot-data', region_name=REGION)
        self.buffer = [] # Memoria temporal para Batching
        self.lat = lat
        self.lon = lon
        
        # --- NUEVO: Estado del Firmware ---
        self.firmware_version = "v1.0.0" # Versión de fábrica
        
        # Variables físicas para simulación realista (Inercia térmica)
        self.offset_temp = random.uniform(-0.5, 0.5)
        self.offset_hum = random.uniform(-1.5, 1.5)
        self.offset_pres = random.uniform(-0.2, 0.2)
        
        # Nota que ahora recibimos argumentos del clima exterior
    def leer_sensor(self, base_temp, base_hum, base_pres, es_anomalia=False):
        
        # 1. Física: Base Global + Bias del Sensor + Ruido Electrónico
        val_temp = base_temp + self.offset_temp + random.uniform(-0.1, 0.1)
        val_hum = base_hum + self.offset_hum + random.uniform(-0.5, 0.5)
        val_pres = base_pres + self.offset_pres + random.uniform(-0.05, 0.05)

        # 2. Inyección de Anomalía Termodinámica
        if es_anomalia:
            val_temp += random.uniform(15, 25) # Sube drásticamente
            val_hum -= random.uniform(15, 25)  # El calor seca el aire (Baja humedad)

        # 3. Empaquetado (Igual que antes, pero usando las vars locales)
        dato = {
            "device_id": self.device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "firmware_version": self.firmware_version,
            "temperature": round(max(0, min(100, val_temp)), 2),
            "humidity": round(max(0, min(100, val_hum)), 2),
            "pressure": round(val_pres, 2), # Presión casi idéntica en todos
            "location": {"lat": self.lat, "lon": self.lon}
        }
        return dato

    def agregar_al_buffer(self, t, h, p, es_anomalia=False):
        # Pasamos los valores hacia abajo
        dato = self.leer_sensor(t, h, p, es_anomalia)
        self.buffer.append(dato)
        logger.info(f"[{self.device_id}] Dato leído: {dato['temperature']}°C (En buffer: {len(self.buffer)})")
        
        
   # --- NUEVA FUNCIÓN: GESTIÓN DE ACTUALIZACIONES (OTA) ---
    def gestionar_ota(self):
        try:
            # 1. Preguntar a AWS si hay una actualización pendiente (Leer Shadow)
            response = self.client.get_thing_shadow(thingName=self.device_id)
            payload = json.loads(response['payload'].read())
            
            # 2. Verificar si hay un estado "desired" (Deseado por el admin)
            if 'state' in payload and 'desired' in payload['state']:
                deseado = payload['state']['desired']
                
                # Si el admin pide una versión diferente a la que tengo...
                if 'firmware_version' in deseado and deseado['firmware_version'] != self.firmware_version:
                    nueva = deseado['firmware_version']
                    
                    # --- SIMULACIÓN DEL PROCESO DE UPDATE ---
                    logger.info(f"📥 [{self.device_id}] DETECTADA ACTUALIZACIÓN OTA: {self.firmware_version} -> {nueva}")
                    time.sleep(1) # Simular tiempo de descarga
                    
                    # Aplicar cambio
                    self.firmware_version = nueva
                    
                    # 3. Confirmar a AWS que ya actualicé (Limpiar el 'desired')
                    confirmacion = {
                        "state": {
                            "reported": {"firmware_version": self.firmware_version},
                            "desired": None # Borra la orden para no repetirla
                        }
                    }
                    self.client.update_thing_shadow(thingName=self.device_id, payload=json.dumps(confirmacion))
                    logger.info(f"✅ [{self.device_id}] ACTUALIZADO EXITOSAMENTE A {self.firmware_version}")

        except Exception:
            pass # Si no hay shadow o falla la red, seguimos operando normal     



    def enviar_batch(self):
        """Envía el paquete completo si el buffer está lleno"""
        if len(self.buffer) >= BATCH_SIZE:
            try:
                payload = json.dumps({"batch": self.buffer})
                
                self.client.publish(
                    topic=TOPIC,
                    qos=1,
                    payload=payload
                )
                
                # ---------------------------------------------------------
                # 2. NUEVO: Actualizar Shadow (Device Twin)
                # ---------------------------------------------------------
                # Tomamos el dato más reciente del buffer para actualizar el estado
                ultimo_dato = self.buffer[-1]
                
                shadow_payload = {
                    "state": {
                        "reported": {
                            "temperature": ultimo_dato["temperature"],
                            "humidity": ultimo_dato["humidity"],
                            "pressure": ultimo_dato["pressure"]
                        }
                    }
                }
                
                # Enviamos el estado al "Gemelo Digital" de AWS
                self.client.update_thing_shadow(
                    thingName=self.device_id,
                    payload=json.dumps(shadow_payload)
                )
                
                logger.info(f"🚀 BATCH ENVIADO Y SHADOW ENVIADOS: {len(self.buffer)} registros de {self.device_id}")
                self.buffer = [] # Limpiar buffer
                self.gestionar_ota()
                
                return True
            except Exception as e:
                logger.error(f"Error: {e}")
                return False
        return False

# --- EJECUCIÓN PRINCIPAL ---
def main():
    # Instanciamos 10 objetos (Sensores)
    sensores = []
    
    #Coordenada Central (Medellín - Universidad Nacional)
    BASE_LAT = 6.261
    BASE_LON = -75.576
    
    #Crear 10 sensores en posiciones FIJAS (Formando una cuadricula o linea)
    for i in range(1, 11):
        
        # Desplazamiento fijo: cada sensro está a 100 m del otro
        offset_lat = (i * 0.001)
        offset_lon = (i * 0.001)
        
        #Coordenadas fijas calculadas
        lat_fija = round(BASE_LAT + offset_lat, 6)
        lon_fija = round(BASE_LON + offset_lon, 6)
        
        sensores.append(SensorIoT(f"sensor_{i:03}", lat_fija, lon_fija))
        print(f"📍 Configurado sensor_{i:03} en {lat_fija}, {lon_fija}")

    logger.info("--- INICIANDO SIMULACIÓN PROFESIONAL (UBICACIONES FIJAS) ---")
    
    ambiente_temp = 22.0
    ambiente_hum = 65.0
    ambiente_pres = 850.0 # hPa realista para Medellín (altura)
    
    try:
        while True:
            # 1. Evolución suave del clima (Caminata aleatoria lenta)
            ambiente_temp += random.uniform(-0.2, 0.2)
            ambiente_hum += random.uniform(-0.5, 0.5)
            
            # Corrección para que no se salga de control (Feedback negativo)
            if ambiente_temp > 28: ambiente_temp -= 0.1
            if ambiente_temp < 18: ambiente_temp += 0.1
            
            # --- AGREGAR ESTO PARA PROTEGER LA HUMEDAD ---
            if ambiente_hum > 90: ambiente_hum -= 0.2
            if ambiente_hum < 40: ambiente_hum += 0.2

            # 2. Ruleta Rusa de Anomalías (10% probabilidad)
            sensores_afectados = []
            if random.random() < 0.1: 
                # Elige 3 sensores al azar
                sensores_afectados = random.sample([s.device_id for s in sensores], 3)
                print(f"⚠️  EVENTO TÉRMICO EN: {sensores_afectados}")

            # 3. Ciclo de lectura
            for sensor in sensores:
                # Verificamos si a este sensor le toca anomalía
                es_anomalia = sensor.device_id in sensores_afectados
                
                # Le pasamos el clima global a cada sensor
                sensor.agregar_al_buffer(ambiente_temp, ambiente_hum, ambiente_pres, es_anomalia)
                sensor.enviar_batch()
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("Simulación detenida.")

if __name__ == "__main__":
    main()
