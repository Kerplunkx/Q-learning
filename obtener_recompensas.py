from collections import OrderedDict
from mongo_connector import obtener_mongo
from influx_connector import get_occupancy, get_amb_temp, get_consume
from datetime import datetime
from q_learning import get_state

N_ESTADOS = 108

#temperaturasI_por_hora
def get_temperatures_by_vote_time():
    """   
        Returns the temperature values when votes were done.
    """
    # Obtener las horas y fechas de los votos y temperaturas de MongoDB
    horas_mongo,_ = obtener_mongo()
    # Obtener las temperaturas internas de InfluxDB
    datos_temperatura = get_amb_temp()
    temperaturas_interna_xhorasdemongo={}
    # Iterar sobre los datos de temperatura
    for dato in datos_temperatura:
        # Obtener solo la parte de la hora de la fecha
        hora = dato['_time'].hour
        # Verificar si la hora está en las horas de MongoDB
        if hora in horas_mongo:
            # Agregar la temperatura al diccionario
            if hora not in temperaturas_interna_xhorasdemongo:
                temperaturas_interna_xhorasdemongo[hora] = []
            #para verificar que si trae correctamente por hora
            #temperaturas_interna_xhorasdemongo[hora].append(dato)
            temperaturas_interna_xhorasdemongo[hora].append(dato["_value"])
    temperaturas_interna_xhorasdemongo = OrderedDict(sorted(temperaturas_interna_xhorasdemongo.items()))

    return datos_temperatura,temperaturas_interna_xhorasdemongo

#ocupancia_por_hora
def get_occupancy_by_vote_time():
    """
        Returns the occupancy values when votes were done.
    """
    # Obtener las horas y fechas de los votos y temperaturas de MongoDB
    horas_mongo,_ = obtener_mongo()
    # Obtener las temperaturas internas de InfluxDB
    datos_ocupante = get_occupancy()
    ocupantes_xhorasdemongo={}
    # Iterar sobre los datos de temperatura
    for dato in datos_ocupante:
        # Obtener solo la parte de la hora de la fecha
        hora = dato['_time'].hour
        # Verificar si la hora está en las horas de MongoDB
        if hora in horas_mongo:
            # Agregar la temperatura al diccionario
            if hora not in ocupantes_xhorasdemongo:
                ocupantes_xhorasdemongo[hora] = []
            #para verificar que si trae correctamente por hora
            #temperaturas_interna_xhorasdemongo[hora].append(dato)
            ocupantes_xhorasdemongo[hora].append(dato["_value"])
    ocupantes_xhorasdemongo = OrderedDict(sorted(ocupantes_xhorasdemongo.items()))

    return datos_ocupante,ocupantes_xhorasdemongo

def get_consume_by_vote_time():
    """
        Returns the consume values when votes were done.
    """
    vote_times, _ = obtener_mongo()
    consumes = get_consume()
    consume_by_time = {}

    for data in consumes:
        hora = data['_time'].hour
        if hora in vote_times:
            if hora not in consume_by_time:
                consume_by_time[hora] = []
            consume_by_time[hora].append(data['_value'])
    consume_by_time = OrderedDict(sorted(consume_by_time.items()))
    return consumes, consume_by_time

#calcular_promedio_temperaturas
def get_avg_temp_by_time() -> dict[int, float]:
    """
        Returns the average temperature by hour
        {hour1: avg_temp1, ...}
    """
    # Obtener las temperaturas por hora
    _,temperaturas_por_hora = get_temperatures_by_vote_time()
    promedios_por_hora = {}
    # Iterar sobre las temperaturas por hora
    for hora, temperaturas in temperaturas_por_hora.items():
        # Calcular el promedio de las temperaturas
        promedio = sum(temperaturas) / len(temperaturas)
        # Agregar el promedio al diccionario
        promedios_por_hora[hora] = promedio
    # Ordenar el diccionario por las claves (horas)
    promedios_por_hora_ordenado = dict(sorted(promedios_por_hora.items()))

    return promedios_por_hora_ordenado

def get_avg_occupancy_by_hour() -> dict[int, float]:
    """
        Returns the average occupancy by hour
        {hour1: avg_occ1, ...}
    """
    # Obtener las temperaturas por hora
    _,ocupantes_por_hora = get_occupancy_by_vote_time()
    promedios_por_hora = {}
    # Iterar sobre las temperaturas por hora
    for hora, ocupantes in ocupantes_por_hora.items():
        # Calcular el promedio de las temperaturas
        promedio = sum(ocupantes) / len(ocupantes)
        # Agregar el promedio al diccionario
        promedios_por_hora[hora] = promedio
    # Ordenar el diccionario por las claves (horas)
    promedios_por_hora_ordenado = dict(sorted(promedios_por_hora.items()))

    return promedios_por_hora_ordenado

def get_avg_consume_by_hour() -> dict[int, float]:
    """
        Returns the average consume by hour
        {hour1: avg_con1, ...}
    """
    _, consume_by_time = get_consume_by_vote_time()
    avg_by_time = {}

    for hora, consumo in consume_by_time.items():
        promedio = sum(consumo) / len(consumo)
        avg_by_time[hora] = promedio

    return dict(sorted(avg_by_time.items()))

#calcular_recompensas_hora_votos
def get_rewards_by_time() -> dict[tuple[datetime, int], int]:
    """
        Returns the reward by time
        {("08:00:00", 20): 0/1, ...}
    """
    # Obtener los datos de la funcion de mongo
    _, votos_temperaturas_por_hora_fecha = obtener_mongo()
    conteos = {}
    # Iterar sobre los datos
    for hora, datos_hora in votos_temperaturas_por_hora_fecha.items():
        for dato_hora in datos_hora:
            voto = dato_hora['voto']
            temp = dato_hora['temp']
            # Si la hora y temperatura no están en el diccionario, agregarlos
            if (hora, temp) not in conteos:
                conteos[(hora, temp)] = {'frio': 0, 'neutral': 0, 'calor': 0}
            # Incrementar el conteo para el tipo de voto
            conteos[(hora, temp)][voto] += 1
    # Calcular los porcentajes
    recompensas_xvotos = {}
    for (hora, temp), conteo in conteos.items():
        total = sum(conteo.values())
        max_voto = max(conteo, key=conteo.get)
        recompensas_xvotos[(hora, temp)] = 1 if max_voto == 'neutral' or conteo['neutral'] >= total * 0.5 else 0

    return recompensas_xvotos

def combinar_datos():
    """
        {hora: {temp: [temp_avg, ocp_avg, reward, cons], temp: [...], ...}}
    """
    # Obtener los promedios de temperaturas y ocupantes
    promedios_temperaturas = get_avg_temp_by_time()
    promedios_ocupantes = get_avg_occupancy_by_hour()
    votos = get_rewards_by_time()
    promedios_consumo = get_avg_consume_by_hour()

    # Crear un diccionario para almacenar los datos combinados
    datos_combinados = {}

    # Iterar sobre los votos
    for (hora, temp), voto in votos.items():
        # Convertir la hora a un entero
        hora = int(hora.split(':')[0])

        # Si la hora no está en el diccionario, agregarla
        if hora not in datos_combinados:
            datos_combinados[hora] = {}

        # Si la hora existe en los promedios, agregar los datos
        if hora in promedios_temperaturas and hora in promedios_ocupantes:
            datos_combinados[hora][temp] = [promedios_temperaturas[hora], promedios_ocupantes[hora], voto, promedios_consumo[hora]]

    return datos_combinados

def estados_recompensas():
    """   
        funcion de recolecta todos los estados que obtengo
    """
    datos_combinados = combinar_datos()
    estados_recompensas = {i: [0] for i in range(1, N_ESTADOS + 1)}

    # Iterar sobre todos los elementos del diccionario
    for hora, datos_hora in datos_combinados.items():
        for temperaturaAC, datos_temp in datos_hora.items():
            # Desempaquetar los datos
            temperaturaI, ocupancia, recompensa, consumo  = datos_temp

            # Crear la lista para pasar a get_state
            lista = [hora, 1, temperaturaAC, temperaturaI, ocupancia, consumo]

            # Llamar a get_state
            estado, _ = get_state(lista,recompensa)

            # Si el estado ya está en el diccionario, agregar la recompensa a la lista de recompensas
            if estado in estados_recompensas:
                estados_recompensas[estado].append(recompensa)
            # Si el estado no está en el diccionario, crear una nueva lista para las recompensas
            else:
                estados_recompensas[estado] = [recompensa]
    diccionario_update=filtro_estados_rep(estados_recompensas)

    return diccionario_update

def filtro_estados_rep(dict_estados_recompensas):
    """
        filtrar estados repetidos
    """
    # Crear un nuevo diccionario para guardar los estados y las recompensas más frecuentes
    nuevos_estados_recompensas = {}
    # Iterar sobre el diccionario de estados y recompensas
    for estado, recompensas in dict_estados_recompensas.items():
        # Contar el número de veces que cada recompensa aparece
        conteo_recompensas = {recompensa: recompensas.count(recompensa) for recompensa in recompensas}
        # Encontrar la recompensa más frecuente
        recompensa_mas_frecuente = max(conteo_recompensas, key=conteo_recompensas.get)
        # Si hay un empate, elegir la recompensa 1
        if conteo_recompensas[recompensa_mas_frecuente] == conteo_recompensas.get(1, 0):
            recompensa_mas_frecuente = 1
        # Agregar el estado y la recompensa más frecuente al nuevo diccionario
        nuevos_estados_recompensas[estado] = recompensa_mas_frecuente
    
    # Devolver el nuevo diccionario
    return nuevos_estados_recompensas

#print("estos son mis estados unicos con sus recompensas: ",estados_recompensas())
