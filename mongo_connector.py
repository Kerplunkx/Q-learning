# import api_connector as api
from datetime import datetime, timedelta
from pymongo import MongoClient
from os import getenv
from dotenv import load_dotenv

load_dotenv()

#Credenciales MongoDB
url_mongo = getenv('MONGO_URL')
puerto_mongo = int(getenv('MONGO_PORT'))
db_mongo = getenv('MONGO_DB')
collection_mongo = getenv('MONGO_COLLECTION')
user_mongo = getenv('MONGO_USER')
pass_mongo = getenv('MONGO_PASS')

def obtener_mongo():
    client = MongoClient(url_mongo, puerto_mongo, username=user_mongo, password=pass_mongo)
    db = client[db_mongo]
    collection = db[collection_mongo]

    datos = collection.find({'estadoAC': 1}).sort('_id', -1)

    horas_mongo=[]
    # diccionario para agrupar los votos y temperaturas por hora y fecha
    votos_temperaturas_por_hora_fecha = {}
    # Iterar sobre los datos obtenidos
    for dato in datos:
        voto = dato['nivelComfort']
        fecha = dato['fecha']
        temp = dato['temperaturaAC']
        # Obtener solo la parte de la hora de la fecha
        hora = fecha.strftime('%H:00:00')
        # Agregar el voto y temperatura al diccionario de horas y fechas
        if hora not in votos_temperaturas_por_hora_fecha:
            votos_temperaturas_por_hora_fecha[hora] = []
        votos_temperaturas_por_hora_fecha[hora].append({'fecha': fecha, 'voto': voto, 'temp': temp})
    # Cerrar la conexión a la base de datos
    client.close()
    # Ordenar el diccionario por las horas
    votos_temperaturas_por_hora_fecha_ordenado = dict(sorted(votos_temperaturas_por_hora_fecha.items()))
    # Imprimir los datos agrupados por hora y fecha
    for indice, (hora, datos_hora) in enumerate(votos_temperaturas_por_hora_fecha_ordenado.items(), start=1):
        #print(f"{indice}.  Hora: {hora} con sus fechas:")
        horas_mongo.append(hora)
        for dato_hora in datos_hora:
            fecha = dato_hora['fecha']
            voto = dato_hora['voto']
            temp = dato_hora['temp']
            #print(f"     Fecha: {fecha}, Voto: {voto}, Temp: {temp}")
    converted_list = [int(time[:2]) for time in horas_mongo]

    return converted_list, votos_temperaturas_por_hora_fecha_ordenado

#obtener_monogo_promedio
def get_neutral_votes_avg(funcion_timedelta: timedelta) -> float:
    """
        Returns the average of the 'neutral' comfort votes in the given time.
    """
    client = MongoClient(url_mongo, puerto_mongo, username=user_mongo, password=pass_mongo)
    db = client[db_mongo]
    collection = db[collection_mongo]

    # Calcular la fecha y hora hace 30 minutos desde ahora
    fecha_y_hora_previa = datetime.now() - funcion_timedelta
    # Realizar la consulta para obtener los datos de los últimos 30 minutos
    datos_ultimos_tiempo_previo = collection.find({"fecha": {"$gte": fecha_y_hora_previa}})
    conteo_total = 0
    conteo_neutral = 0
    # Procesar los datos según sea necesario
    for dato in datos_ultimos_tiempo_previo:
        conteo_total += 1
        # Realizar acciones con cada registro
        if dato['nivelComfort'] == "neutral":
            conteo_neutral += 1
    # Cerrar la conexión a la base de datos
    if conteo_total > 0:
        promedio = conteo_neutral/conteo_total
    else:
        client.close()
        return None
    client.close()
    return promedio
