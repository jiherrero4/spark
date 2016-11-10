#!/usr/bin/env python
# encoding: utf-8
import urllib
import json
import os
import requests
import sys
import webbrowser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

from flask import Flask
from flask import request
from flask import make_response
from flask_restful import Resource, Api
from flaskext.mysql import MySQL

import os.path
import sys

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai


logging.basicConfig(level=logging.DEBUG)

# Flask app should start in global layout
# Flask es un web framework, de forma que podemos programar acciones determinadas basadas
# en que tipo de mensaje web nos llega a nuestra aplicacion
#
#
app = Flask(__name__)

# Utilizamos labels para guardar el identificador de la sala de spark de casa sesión
# Sino lo sabemos vamos a buscarlo..
labels = [["f0b38c60-9a87-11e6-9343-85f91990429b",
               "Y2lzY29zcGFyazovL3VzL1JPT00vM2I5OGI5NTMtMGQyNC0zZDY5LWIyNTMtNzkxNzljOWZkNTVj"]]

bot_email = "Trends2@sparkbot.io"
bot_token = "MDc0OWJkYjgtZWM4Yy00MzgyLThmNDAtNzQ2ZDliMmE1Y2VkMmE5ODM3OWQtMDQ1"
moderator_token = "YjI2NDhkMTYtYjkxMS00ZGYwLWIxNjQtYzQyYTIwOTVhNWI3NDU0YmY2OTYtZjYx"
api_ai_token = "594cb32ae50447938756853f36492b67"


######################################################################################################################
#  Procesamiento de webhooks
#  -  Desde Api.ai
#  -  Desde una sala de Spark
#  -  ...
######################################################################################################################

#  Mensajes que llegan directamente de una sala Spark y van dirigidos al bot
#
@app.route('/webhookSpark', methods=['POST'])
def webhookSpark():

    req = request.get_json(silent=True, force=True)

    print("PASO1: Mensaje recibido desde una spark room:")

    # Con indent lo que hacemos es introducir espacios en el formato de salida
    # de forma que se lea mejor, no simplemente un texto plano..

    data = req.get("data")
    personEmail = data.get("personEmail")
    roomId = data.get("roomId")
    id = data.get("id")

    if (personEmail != bot_email):
      logging.debug(json.dumps(req, indent=4))
      logging.debug("id: ",id)
      message = get_message(bot_token, id)
      text = message.get("text")
      print("Text: ", text)
      response = api_ai_request(text)
      #print("Response:",json.dumps(response, indent=4))
      #fulfillment = response.get("fulfillment")
      result = response.get("result")
      action = result.get("action")
      print("Action:", action)
      processRequestSpark(response, roomId)


    return "OK"
######################################################################################################################
#  Procesamiento de peticiones:
#  -  Desde Api.ai
#  -  Desde una sala de Spark
#  -  ...
######################################################################################################################
def processRequestSpark(req, roomId):
    dato = ""
    # Datos de Acceso del Bot: Token del BOT


    if req.get("result").get("action") == "creaSala":
        creaSalaSpark(moderator_token)

    elif req.get("result").get("action") == "creaGrupo":
        creaGrupoSpark()

    elif req.get("result").get("action") == "llama":
        llamaSala()

    elif req.get("result").get("action") == "gestionado":
        result = req.get("result")
        parameters = result.get("parameters")
        nombreCliente = parameters.get("Clientes")
        tipoInformacion = parameters.get("detalle_de_servicios_gestionados")
        print("Nombre del cliente:",json.dumps(nombreCliente))
        print("tipoInformacion:", json.dumps(tipoInformacion))
        dato = leeExcel(json.dumps(tipoInformacion),json.dumps(nombreCliente))
        status = post_message_markDown(roomId, bot_token, dato)

    elif req.get("result").get("action") == "Inventario":
        dato = leeInventario(req)

    elif req.get("result").get("action") == "Ayuda":
        texto = help_definition()
        status = post_message_markDown(roomId, bot_token,texto)

    elif req.get("result").get("action") == "InformacionSala":
        dato = get_room_sessions_id(req,bot_token,moderator_token)
        status = post_message(dato, bot_token, "probando")
        print (status)

    else:
        return {}

    res = makeWebhookResult(dato)
    return res

#

######################################################################################################################
#  Natural Language:
#  -  Enviamos peticiones a nuestro agente en Api.ai
#  -
#  -  ...
######################################################################################################################

def api_ai_request(query_from_spark):

    ai = apiai.ApiAI(api_ai_token)

    request = ai.text_request()

    request.lang = 'es'  # optional, default value equal 'en'

    # request.session_id = "<SESSION ID, UNIQUE FOR EACH USER>"

    request.query = query_from_spark

    response = request.getresponse()

    print("Response from apiai (instance):", response)
    #print("Respuesta desde Api.ai: ", response.read())

    try:
       #JSONresponse = json.loads(request.getresponse().read().decode('UTF-8'))

       #print("response:", response.read().replace('\n', ''))
       JSONresponse = json.loads(response.read().replace('\n', ''))
       print("JSONresponse:", JSONresponse)
       return JSONresponse
    except Exception as ex:
        print("Error al cargar json:", ex)
        return "Error"



######################################################################################################################
#  Acciones desencadenadas de las peticiones de los clientes
#  -  Crear una sala.
#  -  Conseguir información de una base de datos.
#  -  Mostrar las opciones del asistente.
#  -  ...
######################################################################################################################


def creaSalaSpark(myToken):
    print("funcion creaSalaSpark iniciado")
    roomTitle = "PruebaCreacionSala"
    headers = {"Authorization": "Bearer " + myToken, "Content-type": "application/json"}
    # Define the action to be taken in the HTTP request
    roomInfo = {"title": roomTitle}
    # Execute HTTP POST request to create the Spark Room
    r = requests.post("https://api.ciscospark.com/v1/rooms", headers=headers, json=roomInfo)

    print("funcion creaSalaSpark completado")

    room = r.json()


def creaGrupoSpark():
    print("funcion creaGrupoSpark iniciado")
    myToken = "YjI2NDhkMTYtYjkxMS00ZGYwLWIxNjQtYzQyYTIwOTVhNWI3NDU0YmY2OTYtZjYx"

    # emailFile = userlist.txt
    roomTitle = "Ojete"  # second argument
    # Read the email file and save the emails in an list
    # emails = [line.strip() for line in open(emailFile)]
    emails = ["jiherrero@ttrends.es", "fsobrino@ttrends.es", "pmartin@ttrends.es", "jespejo@ttrends.es",
              "jmvarelad@gmail.com"]

    print("funcion creaGrupoSpark, paso2")

    # Define header used for authentication
    headers = {"Authorization": "Bearer " + myToken,
               "Content-type": "application/json"}

    # Define the action to be taken in the HTTP request
    roomInfo = {"title": roomTitle}

    # Execute HTTP POST request to create the Spark Room
    r = requests.post("https://api.ciscospark.com/v1/rooms", headers=headers, json=roomInfo)
    room = r.json()
    # Print the result of the HTTP POST request
    print(room)

    for email in emails:
        # if it's an blank line don't add:
        if email == "": continue
        # Set the HTTP request payload (action)
        membershipInfo = {"roomId": room["id"],
                          "personEmail": email}
        # Execute HTTP POST request to create the Spark Room
        r = requests.post("https://api.ciscospark.com/v1/memberships",
                          headers=headers, json=membershipInfo)
        membership = r.json()
        print(membership)
        print()


def llamaSala():
    new = 2  # open in a new tab, if possible

    # open a public URL, in this case, the webbrowser docs
    # url = "http://expansion.es"
    url = "https://pxdemo.ttrends.es/webapp/#/?conference=jiherrero@ttrends.es"
    webbrowser.open(url, new=new)


# Lee informacion de un archivo google sheet en la nube
def leeExcel(datoFila, datoColumna):
    # print ("vamos a leer el excel")

    valorBuscado = ""

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-e08df21666bc.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("prueba1")

    worksheet = wks.worksheet("gestionados")

    valor_datoFila = worksheet.find(datoFila)
    valor_datoColumna = worksheet.find(datoColumna)

    row = valor_datoFila.row
    column = valor_datoColumna.col

    # print("row: ",row, "column: ",column)

    valorBuscado = worksheet.cell(row, column).value

    print("valor Buscado: ", valorBuscado)

    return valorBuscado


def leeInventario(req):
    datos_inventario = parameters.get("datos_inventario")




######################################################################################################################
#  Funciones sobre salas de Spark
#  -  Conseguir identificadores de sala
#  -  Leer mensajes de las salas
#  -  ...
######################################################################################################################


# El objetivo de esta función es asociar el número de la sesión que nos envía api.ai
# con el identificador de sala de spark (que no envía api.ai)
# Mapeando el id de la sesión con el id de la sala el envio de mensajes a la sala
# puede ser directo y más eficiente.
def get_room_sessions_id(req,bot_token,moderator_token):

    sessionId = req.get("sessionId")

    for c in range(len(labels)):
       if (labels[c][0] == sessionId):
          print("ya dispongo del identificador de la sala, lo envio...")
          return labels[c][1]

    else:
        roomId = informacionSala(req,bot_token,moderator_token)
        labels.append([sessionId,roomId])
        print("Anadiendo un nuevo identificador de sesion: ", sessionId, "-> con roomId: ",roomId)
        return roomId

def informacionSala(req,bot_token,moderator_token):

    identificador_sala = get_bot_room_id(req,bot_token,moderator_token)
    print ("el identificador de esta sala es: ", identificador_sala)
    return identificador_sala


def get_bot_room_id(req,bot_token,moderator_token):

    result = req.get("result")
    ultima_peticion= result.get("resolvedQuery")
    identificador_sala = get_rooms(ultima_peticion,bot_token,moderator_token)

    return identificador_sala

def get_rooms(ultima_peticion,bot_token,moderator_token):

    header = {'Authorization': "Bearer "+ bot_token, 'content-type': 'application/json'}

    result = requests.get(url='https://api.ciscospark.com/v1/rooms', headers=header)

    JSONresponse = result.json()
    roomlist_array = []

    for EachRoom in JSONresponse['items']:
        roomlist_array.append(EachRoom.get('title') + ' ** ' + EachRoom.get('id'))
        last_message = get_last_message(EachRoom.get('id'),bot_token,moderator_token)
        print("Last Message:", last_message)

        if (last_message.__contains__(ultima_peticion)):
          return EachRoom.get('id')

    return "sala no encontrada"
    #print("Rooms:", roomlist_array)

def get_last_message(roomid,bot_token,moderator_token):

    num_mensajes = 2
    header = {'Authorization': "Bearer "+ bot_token, 'content-type': 'application/json'}
    payload = {'roomId': roomid, 'max': num_mensajes}

    result = requests.get(url='https://api.ciscospark.com/v1/messages', headers=header,params=payload)

    # en caso de fallo en el acceso al último mensaje, es que es una sala grupal, y el bot no tiene permisos para conseguir los mensajes
    # tendrá que ser un moderador (no un bot) que este presente en la sala grupal para acceder a los mensajes
    if result.status_code != 200:
        header = {'Authorization': "Bearer " + moderator_token , 'content-type': 'application/json'}
        payload = {'roomId': roomid, 'max': num_mensajes}

        result = requests.get(url='https://api.ciscospark.com/v1/messages', headers=header, params=payload)

        # si vuelve a fallar, entonces no podemos conseguir la información y por tanto el id de la sala...
        if result.status_code != 200:
           return ""



    JSONresponse = result.json()
    messagelist_array = []
    #print (JSONresponse)

    for EachMessage in JSONresponse['items']:
       messagelist_array.append(EachMessage.get('text'))

    #print("Messages:",messagelist_array)

    return messagelist_array[0]

def get_session_id(req):

    session_id = req.get("sessionId")

    return session_id

def post_message(roomid,bot_token,text):

    header = {'Authorization': "Bearer " + bot_token, 'content-type': 'application/json'}
    payload = {'roomId': roomid, 'text': text}

    print("RoomId:", roomid)
    print("Bottoken: ", bot_token)

    result = requests.post(url='https://api.ciscospark.com/v1/messages', headers=header, json=payload)

    # en caso de fallo en el acceso al último mensaje, es que es una sala grupal, y el bot no tiene permisos para conseguir los mensajes
    # tendrá que ser un moderador (no un bot) que este presente en la sala grupal para acceder a los mensajes
    if result.status_code != 200:
        return result.json()
        print ("RoomId:",roomid)
        print ("Bottoken: ", bot_token)
    else:
        return "mensaje enviado correctamente..."

def post_message_markDown(roomid,bot_token,markdown):

    header = {'Authorization': "Bearer " + bot_token, 'content-type': 'application/json'}
    payload = {'roomId': roomid, 'markdown': markdown}

    print("RoomId:", roomid)
    print("Bottoken: ", bot_token)

    result = requests.post(url='https://api.ciscospark.com/v1/messages', headers=header, json=payload)

    # en caso de fallo en el acceso al último mensaje, es que es una sala grupal, y el bot no tiene permisos para conseguir los mensajes
    # tendrá que ser un moderador (no un bot) que este presente en la sala grupal para acceder a los mensajes
    if result.status_code != 200:
        return result.json()
        print ("RoomId:",roomid)
        print ("Bottoken: ", bot_token)
    else:
        return "mensaje enviado correctamente..."

def get_message(bot_token, id):

    header = {'Authorization': "Bearer " + bot_token, 'content-type': 'application/json'}

    result = requests.get(url='https://api.ciscospark.com/v1/messages/'+ id, headers=header)

    if result.status_code != 200:
       print("Error al leer mensaje")

    JSONresponse = result.json()
    print(JSONresponse)
    return JSONresponse



######################################################################################################################
#  Definicion de opciones y dialogos con los clientes
#  - Mensaje de ayuda
#  - Mensaje por defecto en caso de no encontrar la respuesta.
######################################################################################################################

#  Definición de  las opciones de ayuda.
def help_definition():

    text = "Hola, soy Andy! \nEstos son los temas sobre los que te puedo ayudar: \n 1. **Informes de estadisticas.**\n 2. **Informacion de inventario** \n 3. **Actas de reuniones**\n 4. **Soporte Techno Trends**"

    return text


def makeWebhookResult(data):
    # print ("preparando el mensaje de vuelta")

    if data is None or data == "":
        speech = "no he encontrado lo que me pides, por favor especifica mas tu peticion..."
    else:
        speech = data

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "from spark"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
