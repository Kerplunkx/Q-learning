import pytz
from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta
from os import getenv
from dotenv import load_dotenv

load_dotenv()

url_influx = getenv('INFLUX_URL')
token_influx = getenv('INFLUX_TOKEN')
org_influx = getenv('INFLUX_ORG')
bucket1_influx = getenv('BUCKET1')
bucket2_influx = getenv('BUCKET2')
bucket3_influx = getenv('BUCKET3')


def get_last_values() -> list[datetime, int, int, float, int, float]:
    """
        Returns a list with the last stored values.
        ([fecha_y_hora_actual, estado_AC, temperatura_seteada, temperatura_estacion, ocupancia, consumo])
    """
    # Conectarse al cliente de InfluxDB
    influx_client = InfluxDBClient(url=url_influx, token=token_influx, org=org_influx)
    fields_influx = ["estado","temp_set","temperatura"]
    valores=[]
    valores.append(datetime.now(pytz.timezone('America/Guayaquil')))
    for field in fields_influx:
        # Construir la consulta
        query = f'from(bucket:"{bucket1_influx}") \
                |> range(start: -5d) \
                |> filter(fn: (r) => r._field == "{field}" and r._measurement == "stationChicaNoboa" and r.Ubicacion == "LST") \
                |> last()'
        # Ejecutar la consulta
        result = influx_client.query_api().query(org=org_influx, query=query)
        # Obtener los registros
        records = list(result)
        for record in records:
            for row in record.records:
                valor=row.values.get("_value")
                #Descomentar estas lineas si se quiere obtener las temperaturas desde la api
                #if field=="temp_set":
                #    valor=api.obtener_temperatura_actual()
                valores.append(valor)
    
    query = f'from(bucket:"{bucket2_influx}") \
            |> range(start: -5d) \
            |> filter(fn: (r) => r._field == "count" and r._measurement == "person_count") \
            |> last()'
    # Ejecutar la consulta
    result = influx_client.query_api().query(org=org_influx, query=query)
    # Obtener los registros
    records = list(result)
    for record in records:
        for row in record.records:
            valor=row.values.get("_value")
            valores.append(valor)

    query = f'from(bucket:"{bucket3_influx}") \
            |> range(start: -5d) \
            |> filter(fn: (r) => r._field == "energia" and r._measurement == "energia") \
            |> last()'
    # Ejecutar la consulta
    result = influx_client.query_api().query(org=org_influx, query=query)
    # Obtener los registros
    records = list(result)
    for record in records:
        for row in record.records:
            valor=row.values.get("_value")
            valores.append(valor)


    # Cerrar la conexión
    influx_client.close()
    return valores

def get_occupancy():
    """
        Returns the occupancy of the LST from the last 30 days.
        [{'position': value, '_time': value, '_value'}]
    """
    client = InfluxDBClient(url=url_influx, token=token_influx, org=org_influx)
    query = f"""from(bucket:"{bucket2_influx}") |> range(start: -30d) |> filter(fn: (r) => r._field == "count" 
            and r._measurement == "person_count") |> filter(fn: (r) => r["_value"] >0 ) |> timeShift(duration: -5h) |> yield(name: "all")
            """
    valores=[]
    # Ejecutar la consulta
    result = client.query_api().query(org=org_influx, query=query)
    # Obtener los registros
    records = list(result)
    # Imprimir los datos obtenidos
    for record in records:
        for i, row in enumerate(record.records, start=1):  # Agregar un contador con inicio en 1
            valor=row.values.get("_value")
            tiempo=row.values.get("_time")
            valores.append({"position": i, "_time": tiempo, "_value": valor})
                # Cerrar la conexión
    client.close()
    return valores
 
def get_amb_temp():
    """
        Returns the amb. temperature of the LST from the last 31 days.
        [{'position': value, '_time': value, '_value'}]
    """
    valores =[]
    client = InfluxDBClient(url=url_influx, token=token_influx, org=org_influx)
    query = f"""from(bucket:"{bucket1_influx}") |> range(start: -31d) |> filter(fn: (r) => r._field == "temperatura" 
                and r._measurement == "stationChicaNoboa" and r.Ubicacion == "LST") |> timeShift(duration: -5h)|> yield(name: "all")
            """
    # Ejecutar la consulta
    result = client.query_api().query(org=org_influx, query=query)
    # Obtener los registros
    records = list(result)
    # Imprimir los datos obtenidos
    for record in records:
        for i, row in enumerate(record.records, start=1):  # Agregar un contador con inicio en 1
            valor=row.values.get("_value")
            tiempo=row.values.get("_time")
            valores.append({"position": i, "_time": tiempo, "_value": valor})
    # Cerrar la conexión
    client.close()
    return valores

def get_consume():
    """
        Returns the AC consume from the last 30 days.
    """
    client = InfluxDBClient(url=url_influx, token=token_influx, org=org_influx)
    query = f"""from(bucket:"{bucket3_influx}") |> range(start: -30d) |> filter(fn: (r) => r._field == "energia" 
                and r._measurement == "energia") |> timeShift(duration: -5h)|> yield(name: "all")
            """
    valores = []

    result = list(client.query_api().query(org=org_influx, query=query))
    for record in result:
        for i, row in enumerate(record.records, start=1):
            valor = row.values.get("_value")
            tiempo = row.values.get("_time")
            valores.append({"position": i, "_time": tiempo, "_value": valor})
    client.close()
    return valores

def get_avg_last_hour_consume() -> float:
    """
        Returns the average consume for the last hour.    
        Starts by the current time.
    """
    client = InfluxDBClient(url=url_influx, token=token_influx, org=org_influx)
    query = f"""from(bucket:"{bucket3_influx}") 
            |> range(start: -1h) 
            |> filter(fn: (r) => r._field == "energia" and r._measurement == "energia") 
            |> mean()
            """
    result = client.query_api().query(org=org_influx, query=query)
    result = result.to_values(columns=['_value'])
    return result[0][0]
