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

from flask import Flask
from flask import request
from flask import make_response
from flask_restful import Resource, Api
from flaskext.mysql import MySQL

# Flask app should start in global layout
# Flask es un web framework, de forma que podemos programar acciones determinadas basadas
# en que tipo de mensaje web nos llega a nuestra aplicacion
#
#
app = Flask(__name__)


# Ahora vamos a definir que hacer si nuestra aplicacion recibe un webhook tipo POST
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("PASO1: Request recibido de api.ai:")

    # Con indent lo que hacemos es introducir espacios en el formato de salida
    # de forma que se lea mejor, no simplemente un texto plano..
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    # Transformo res a un formato json tabulado.
    res = json.dumps(res, indent=4)
    # print(res)
    # La respuesta tiene que ser tipo application/json
    # La funcion make_response pertenece a la libreria de Flask
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


# En esta funcion vamos a procesar el mensaje que hemos recibido, webhook (post).
# Lo primero que vamos a buscar es la accion a realizar.
#
#
def processRequest(req):
    dato = ""
    # Datos de Acceso del Bot: Token del BOT
    bot_token = "MDc0OWJkYjgtZWM4Yy00MzgyLThmNDAtNzQ2ZDliMmE1Y2VkMmE5ODM3OWQtMDQ1"

    # Datos de Acceso de un moderador, me he puesto a mí por defecto. Es útil ya que el bot tiene ciertas limitaciones
    # de acceso a datos (configuradas por seguridad por Cisco)
    moderator_token = "YjI2NDhkMTYtYjkxMS00ZGYwLWIxNjQtYzQyYTIwOTVhNWI3NDU0YmY2OTYtZjYx"

    if req.get("result").get("action") == "creaSala":
        creaSalaSpark()

    elif req.get("result").get("action") == "creaGrupo":
        creaGrupoSpark()

    elif req.get("result").get("action") == "llama":
        llamaSala()

    elif req.get("result").get("action") == "gestionado":
        dato = leeExcel(req)

    elif req.get("result").get("action") == "Inventario":
        dato = leeInventario(req)

    elif req.get("result").get("action") == "Ayuda":
        dato = proporcionaAyuda(req)

    elif req.get("result").get("action") == "InformacionSala":
        dato = informacionSala(req,bot_token,moderator_token)

    else:
        return {}

    res = makeWebhookResult(dato)
    return res


def creaSalaSpark():
    print("funcion creaSalaSpark iniciado")
    myToken = "YjI2NDhkMTYtYjkxMS00ZGYwLWIxNjQtYzQyYTIwOTVhNWI3NDU0YmY2OTYtZjYx"
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


# Lee informacion de un archivo excel
def leeExcel(req):
    # print ("vamos a leer el excel")

    valorBuscado = ""
    result = req.get("result")
    parameters = result.get("parameters")
    nombreCliente = parameters.get("Clientes")
    tipoInformacion = parameters.get("detalle_de_servicios_gestionados")

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-e08df21666bc.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("prueba1")

    worksheet = wks.worksheet("gestionados")

    cliente = worksheet.find(nombreCliente)
    servicio = worksheet.find(tipoInformacion)

    column = cliente.col
    row = servicio.row

    # print("row: ",row, "column: ",column)

    valorBuscado = worksheet.cell(row, column).value

    print("valor Buscado: ", valorBuscado)

    return valorBuscado


def leeInventario(req):
    datos_inventario = parameters.get("datos_inventario")


def informacionSala(req,bot_token,moderator_token):

    identificador_sala = get_bot_room_id(req,bot_token,moderator_token)
    print ("el identificador de esta sala es: ", identificador_sala)
    return identificador_sala

def proporcionaAyuda(req):
    ayuda = "Esto es una \n prueba"

    return ayuda


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
