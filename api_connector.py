import requests
from dotenv import load_dotenv
from os import getenv

load_dotenv()

api_url = getenv("API_URL")

def obtener_temperatura_actual() -> int:
    """
        Performs a GET request to the API and returns
        the current temperature.
    """
    resp = requests.get(api_url+'temp').json()
    return int(resp['Message'])

def obtener_estado_actual() -> int:
    """
        Performs a GET request to the API and returns
        the current status (off/on) of the AC.
    """
    resp = requests.get(api_url+'estado').json()
    return int(resp['Message'])

def cambiar_temperatura_actual(nueva_temperatura: int):
    """
        Performs a PATCH request to the API and changes
        the current temperature of the AC.
    """
    if nueva_temperatura >= 16 and nueva_temperatura <=24:
        requests.patch(url = api_url+'temp/'+str(nueva_temperatura))

def cambiar_estado_actual(nuevo_estado: int):
    """
        Performs a PATCH request to the API and changes
        the current status (off/on) of the AC.
    """
    if nuevo_estado == 0 or nuevo_estado == 1:
        requests.patch(url = api_url+'estado/'+str(nuevo_estado))
