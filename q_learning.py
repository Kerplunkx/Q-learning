import os
import time
import utils
import numpy as np
import mongo_connector as mc
import influx_connector as ic
import api_connector as api
import obtener_recompensas as r
from datetime import datetime, timedelta
from mqtt_conf import run_publisher 
from itertools import product

#Constantes
N_ACCIONES = 3
N_ESTADOS = 108
N_EPISODIOS = 20
N_PASOS = 30
#Acciones
UP = 2
DOWN = 1
MAINTAIN = 0

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

ocupancia_list = ['POCA', 'MEDIA', 'MUCHA']
temp_in_list = ['T1', 'T2']
temp_ac_list = ['FRIO', 'NEUTRAL', 'CALOR']
periodo_list = ['P1', 'P2', 'P3']
consumo_ac = ['ALTO', 'BAJO']

ESTADOS = list(product(ocupancia_list, temp_in_list, temp_ac_list, periodo_list, consumo_ac))

def get_actions(estado: int) -> list[int]:
    """
        Funcion que devuelve las acciones disponibles dependiendo de la temperatura actual del A/C
    """
    acciones = [MAINTAIN]
    temp = api.obtener_temperatura_actual()
    promedio_consumo = ic.get_avg_last_hour_consume()

    if ESTADOS[estado - 1][2] == "NEUTRAL": 
        acciones.append(MAINTAIN)
    if ESTADOS[estado - 1][2] == "FRIO":
        if temp !=  16 and promedio_consumo <= 40:
            acciones.append(DOWN)
        else:
            acciones.append(UP)
    if ESTADOS[estado - 1][2] == "CALOR":
        if temp !=  24 and promedio_consumo <= 40:
            acciones.append(UP)
        else:
            acciones.append(DOWN)
                          
    return acciones

def get_state (lista_de_valores: list[str], recompensa: int) -> tuple[int, int]:
    """
        Funcion que devuelve el estado actual del LST. 
        La lista que recibe esta funcion debe tener el siguiente orden 
        ([fecha_y_hora_actual, estado_AC, temperatura_seteada, temperatura_estacion, ocupancia, consumo])
    """
    assert len(lista_de_valores) == 6, f"get_state list expected len of 6, but got {len(lista_de_valores)}"

    periodo = utils.get_day_period_label(lista_de_valores[0])
    temperatura_ac = utils.get_ac_temp_label(lista_de_valores[2])
    temperatura_interna = utils.get_amb_temp_label(lista_de_valores[3])
    ocupancia = utils.get_occupancy_label(lista_de_valores[4])
    consumo= utils.get_consume_label(lista_de_valores[5])

    return (ESTADOS.index((ocupancia, temperatura_interna, temperatura_ac, periodo, consumo)) + 1, recompensa)

def get_next_state(accion: int, temperatura: int) -> tuple[tuple[int, int], int]:
    """
        Applies the action chosen by the model.
    """
    assert 16 <= temperatura <= 24, f"get_next_state expected a 'temperatura' in the range [16, 24] but got {temperatura}"

    if accion == 0:
        return get_state(ic.get_last_values(), None), temperatura
    elif accion == 1:
        api.cambiar_temperatura_actual(temperatura-2)
        return get_state(ic.get_last_values(), None), temperatura-2
    elif accion == 2:
        api.cambiar_temperatura_actual(temperatura+2)
        return get_state(ic.get_last_values(), None), temperatura+2

def get_reward(estado: int) -> int:
    promedio = mc.get_neutral_votes_avg(timedelta(minutes=60))
    if promedio is not None:
        #obtener recompensa online
        if promedio >= 0.5:
            return 1
        else:
            return 0
    else:
        #obtener recompensa offline
        diccionario = r.estados_recompensas()
        recompensa = diccionario[estado]
        return recompensa

def get_consume_reward(estado: int) -> int:
    """
       Calculates a reward based on consumption level. 
    """
    return 1 if ic.get_avg_last_hour_consume() or 0 <= 40 else 0
    
def qlearning(alpha: float, gamma: float, epsilon: float, tau: float = 0.5, tabla_probabilidades = None, tabla_q = None, tabla_politicas = None):
    now = datetime.now()
    day_of_week = now.weekday()
    hour = now.hour

    print("el dia es: ", day_of_week)
    if 0 <= day_of_week <= 4:
        #Inicializar tabla de probabilidades estocasticas para cada accion
        if tabla_probabilidades is None:
            pi_q = {k:[1/len(get_actions(k)) for a in range(len(get_actions(k)))] for k in range(1, N_ESTADOS + 1)}
        else:
            pi_q = tabla_probabilidades
        
        #inicializar diccionario con valores q para todos los estados, diccionario se inicializa en 0
        if tabla_q is None:
            q_table = {k:[0 for a in range(len(get_actions(k)))] for k in range(1, N_ESTADOS + 1)}
        else:
            q_table = tabla_q

        #Inicializar tabla de politicas, se inicializa en 0
        if tabla_politicas is None:
            pi = np.zeros((N_ESTADOS, 1), dtype=np.int32)
        else:
            pi = tabla_politicas

        temp_actual = api.obtener_temperatura_actual()
        temp_anterior = temp_actual
        temp_q = temp_anterior
        #print("la temp actual antes de iniciar paso es: ", temp_actual)
        #print("la temp anterior antes de iniciar paso es: ", temp_anterior)

        print("\n")
        for epi in range(N_EPISODIOS):
            print("iniciando episodio:", epi)
            for t in range(N_PASOS):
                print("iniciando paso:", t)
                hour = datetime.now().hour
                print("La hora es: ", hour)
                if 8 <= hour < 18:
                    if api.obtener_estado_actual() == 1:
                        temp_actual = api.obtener_temperatura_actual()
                        print("la temp actual es: ", temp_actual)
                        print("la temp anterior es: ", temp_anterior)
                        print("la temp q es: ", temp_q)
                        if (temp_q != temp_actual):
                            print("HUBO UN CAMBIO MANUAL")
                            temp_q = temp_actual 
                            temp_anterior = temp_actual
                            time.sleep(60*30)
                        else:
                            print("usando algortimo...")
                            #Esto se realiza cuando el usuario no ha hecho nada
                            time.sleep(60) #Tiempo en segundos.

                            #Obtener estado del LST (ultimos valores registrados en influx)
                            lista = ic.get_last_values()
                            print("variables: ", lista)
                            estadoActualLST,_ = get_state(lista, None)
                            print("el estado actual es: ", estadoActualLST) 
                            #Obtener acciones con la temperatura acutual del A/C del LST (API)
                            acciones = get_actions(estadoActualLST)
                            print("Estas son las acciones disponibles: ", acciones)
                            #Obtener accion random con la lista de acciones obtenidos previamente
                            prob = pi_q[estadoActualLST]
                            print("Probabilidades: ", prob)
                            accion = np.random.choice(acciones, p=prob)
                            #Obtenemos el siguiente estado
                            nuevo_estado_LST, temp_q = get_next_state(accion, temp_actual)
                            print("La accion realizada es: ", accion)
                            print("El indice de la accion es: ", acciones.index(accion))
                            #print("La temperatura anterior es: ", temp_anterior ) 
                            #obtenemos recompensa
                            recompensa = get_reward(nuevo_estado_LST[0])
                            recompensa_consumo = get_consume_reward(nuevo_estado_LST[0])
                            recompensa = ((1 - tau) * (recompensa_consumo)) + (tau * recompensa)
                            print("La recompensa es: ", recompensa) 

                            #Actualizar tabla Q
                            print("esto q_table del estado actual: ",q_table[estadoActualLST])
                            p1=q_table[estadoActualLST][acciones.index(accion)]
                            #print("p1 es: ", p1)
                            p2=np.max(q_table[nuevo_estado_LST[0]])
                            #print("p2 es: ", p2)
                            q_table[estadoActualLST][acciones.index(accion)] =  p1+ alpha * (recompensa + gamma*p2 - p1)
                            print("Estos son los nuevos valores q: ", q_table[estadoActualLST])

                            #Determinar accion optima
                            accion_optima = q_table[estadoActualLST].index(max(q_table[estadoActualLST]))
                            print("La accion optima es: ", accion_optima)
                            try:
                                indice_accion_optima = acciones.index(accion_optima)
                            except:
                                indice_accion_optima = 1
                            print("El indice de la accion optima es: ", indice_accion_optima)
                            run_publisher(estadoActualLST, acciones, int(accion))

                            #Guardar accion optima en tabla pi
                            pi[estadoActualLST - 1] = accion_optima

                            #//WARNING: PROB PROBLEM
                            for i in range(len(acciones)):
                                if i == indice_accion_optima:
                                    pi_q[estadoActualLST][i] = 1 - epsilon + epsilon/len(acciones)
                                else:
                                    pi_q[estadoActualLST][i] = epsilon/len(acciones)
                                    
                            
                            print("Estas son las nuevas probabilidades: ", pi_q[estadoActualLST])
                            #muerte=np.random.choice(acciones, p=pi_q[estadoActualLST])
                            temp_anterior = temp_actual                              
                    else:
                        print("Esperando a que se encienda el aire...")
                        print("este es el estado: ", api.obtener_estado_actual())
                        if api.obtener_estado_actual() == 1:
                            temp_q = api.obtener_temperatura_actual()
                        pass
                else:
                    print("Esperando a que sean las 8:00 AM")
                    if hour>=18:
                        calculo = 32-hour
                    else:
                        calculo = 8-hour
                    print("Dormire "+ str(calculo) + " horas")
                    time.sleep(60*60*calculo) #Tiempo en segundos. (14-1 hora)
                print("\n")
            if api.obtener_estado_actual() == 1 and 8 <= hour < 18: #REVISAR ESTE IF
                #print("aqui entro a guardar")
                utils.save_tables(q_table, pi_q, pi, THIS_DIR + "/csv_files/last_tables.csv")
                utils.save_all_tables(q_table, pi_q, pi, THIS_DIR + "/csv_files/hitorical_record.csv")
                #print("guarde")
        return q_table, pi_q, pi

    else:
        time.sleep(60*60*24) #Tiempo en segundos. (1 dia)
        return tabla_q, tabla_probabilidades, tabla_politicas

                    
def main():
    directorio_existe = utils.create_directory("csv_files")
    if not directorio_existe:
        try:
            lista = utils.import_tables(THIS_DIR + "/csv_files/last_tables.csv") #(tabla_q, tabla_prob, tabla_pi)
            tabla_q = lista[0]
            tabla_prob = lista[1]
            tabla_pi = lista[2]
        except FileNotFoundError:
            tabla_q = tabla_prob = tabla_pi = None
            print("No se encontro tablas iniciales, iniciando aprendizaje...")
        
        while True:
            #El valor alpha determina que tan rapido se obtienen los valores q. El valor gamma determina la ponderacion de las recompensas futuras con respecto a la recompensa inmediata \
            #El valor epsilon determina la probabilidad de explorar. 
            tabla_q, tabla_prob, tabla_pi = qlearning(alpha=0.3, gamma=0.9, epsilon=0.9, tabla_probabilidades=tabla_prob, tabla_q=tabla_q, tabla_politicas=tabla_pi)
        else:
            return
        
if __name__ == "__main__":
    main()
