import os 
import csv
from datetime import datetime

def get_day_period_label(date: datetime) -> str:
    """
        Returns the day period (P1, P2, P3) from the given argument.
    """
    if type(date) == datetime:
        if date.hour >= 8 and date.hour < 11:
            periodo = 'P1'
        elif date.hour >= 11 and date.hour < 14:
            periodo = 'P2'
        elif date.hour >= 14 and date.hour <= 18:
            periodo = 'P3'
    else:
        if date >= 8 and date < 11:
            periodo = 'P1'
        elif date >= 11 and date < 14:
            periodo = 'P2'
        elif date >= 14 and date <= 18:
            periodo = 'P3'
    return periodo

def get_ac_temp_label(temp: float) -> str:
    """        
        Returns the AC temp label(FRIO, CALOR, NEUTRAL) from the given argument.
    """
    if temp >= 16.0 and temp < 20.0:
        temperatura_ac = 'FRIO'
    elif temp >= 20.0 and temp < 23.0:
        temperatura_ac = 'NEUTRAL'
    elif temp >= 23.0 and temp <= 24.0:
        temperatura_ac = 'CALOR'
    return temperatura_ac


def get_amb_temp_label(temp: float) -> str:
    """        
        Returns the amb temp label (T1, T2) from the given argument.
    """
    # if lista_de_valores[3] >= 21.0 and lista_de_valores[3] < 24.0:
    if temp >= 14.0 and temp < 24.0:
        temperatura_interna = 'T1'
    elif temp >= 24.0: # and temp <= 27.0:
        temperatura_interna = 'T2'
    return temperatura_interna

def get_occupancy_label(occup: float) -> str:
    """        
        Returns the occupancy label (POCA, MEDIA, MUCHA) from the given argument.
    """
    if occup >= 0.0 and occup < 7.0:
        ocupancia = 'POCA'
    elif occup >= 7.0 and occup < 14.0:
        ocupancia = 'MEDIA'
    elif occup >= 14.0 and occup <= 20.0:
        ocupancia = 'MUCHA'
    return ocupancia

def get_consume_label(consume: float) -> str:
    """        
        Returns the consume label (BAJO, ALTO) from the given argument.
    """
    if consume < 40.0:
        consumo = "BAJO"
    else:
        consumo = "ALTO"
    return consumo
    
def save_tables(tabla_q, tabla_prob, tabla_pi, nombre_archivo: str):
    with open(nombre_archivo, 'w', newline='') as archivo_csv:
        #Crear el escritor CSV
        escritor_csv = csv.writer(archivo_csv)

        #Guardar Tabla q
        escritor_csv.writerow(["Tabla_q", datetime.now()])
        for i in tabla_q.keys():
            num_datos=len(tabla_q[i])
            fila=[]
            fila.append(i)
            for dato in range(0,num_datos):
                fila.append(tabla_q[i][dato])
            escritor_csv.writerow(fila)
        
        #Guardar Tabla de probabilidades
        escritor_csv.writerow(["Tabla_prob", datetime.now()])
        for i in tabla_prob.keys():
            num_datos=len(tabla_prob[i])
            fila=[]
            fila.append(i)
            for dato in range(0,num_datos):
                fila.append(tabla_prob[i][dato])
            escritor_csv.writerow(fila)

        #Guardar tabla de politicas
        escritor_csv.writerow(["Tabla_pi", datetime.now()])
        for i in range(0, len(tabla_pi)):
            fila=[int(i)+1,int(tabla_pi[i])]
            escritor_csv.writerow(fila)

def save_all_tables(tabla_q, tabla_prob, tabla_pi, nombre_archivo: str):
    #Abrir el archivo en modo de escritura
    with open(nombre_archivo, 'a', newline='') as archivo_csv:
        #Crear el escritor CSV
        escritor_csv = csv.writer(archivo_csv)

        #Guardar Tabla q
        escritor_csv.writerow(["Tabla_q", datetime.now()])
        for i in tabla_q.keys():
            num_datos=len(tabla_q[i])
            fila=[]
            fila.append(i)
            for dato in range(0,num_datos):
                fila.append(tabla_q[i][dato])
            escritor_csv.writerow(fila)
        
        #Guardar Tabla de probabilidades
        escritor_csv.writerow(["Tabla_prob", datetime.now()])
        for i in tabla_prob.keys():
            num_datos=len(tabla_prob[i])
            fila=[]
            fila.append(i)
            for dato in range(0,num_datos):
                fila.append(tabla_prob[i][dato])
            escritor_csv.writerow(fila)

        #Guardar tabla de politicas
        escritor_csv.writerow(["Tabla_pi", datetime.now()])
        for i in range(0, len(tabla_pi)):
            fila=[int(i)+1,int(tabla_pi[i])]
            escritor_csv.writerow(fila)

def import_tables(nombre_archivo: str):
    """    
        Se retornan las tablas en el siguiente orden
        (tabla_q, tabla_prob, tabla_pi)
    """
    diccionarios = []
    bloque_actual = None

    with open(nombre_archivo, 'r', newline='') as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        strings_a_buscar=["Tabla_q", "Tabla_prob", "Tabla_pi"]

        nombre_tabla = ""
        for fila in lector_csv:
            #print(fila)
            if (any(fila[0] == s for s in strings_a_buscar)):
                nombre_tabla=fila[0]
                bloque_actual = {}
                if nombre_tabla == "Tabla_pi":
                    bloque_actual = []
                diccionarios.append(bloque_actual)
            else:
                clave = fila[0]
                clave_int = int(clave)
                if nombre_tabla == "Tabla_pi":
                    valor_int = int(fila[1])
                    #print(clave_int)
                    bloque_actual.append(valor_int)
                else:
                    lista=[]
                    for i in range(1, len(fila)):
                        valor_float = float(fila[i])
                        lista.append(valor_float)
                    bloque_actual[clave_int] = lista
    return diccionarios

def create_directory(nombre_directorio):
    """
        Creates directory in case it doesn't  exist.
    """
    directorio_script = os.path.dirname(__file__)
    ruta_completa = os.path.join(directorio_script, nombre_directorio)
    
    if os.path.exists(ruta_completa):
        return 0
    else:
        try:
            os.makedirs(ruta_completa, exist_ok=True)
            return 0
        except OSError as error:
            return 1


def comparacion_visual_calculo_porcentajeshxv():
    """ 
        esta funcion es para ver los porcentajes de votos por temperatura y hora y poder comparar 
        que la funcion calcular_recompensas_hora_votos este dando porcentajes correctos en cuanto 
        a recompensa 
    """
    # Obtener los datos de MongoDB
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
    porcentajes_visuales = {}
    for (hora, temp), conteo in conteos.items():
        total = sum(conteo.values())
        porcentajes_visuales[(hora, temp)] = {voto: (count / total) * 100 for voto, count in conteo.items()}

    return porcentajes_visuales
