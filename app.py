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


bot_email = "Trends2@sparkbot.io"
bot_token = "MDc0OWJkYjgtZWM4Yy00MzgyLThmNDAtNzQ2ZDliMmE1Y2VkMmE5ODM3OWQtMDQ1"
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
      print("id: ",id)
      message = get_message(bot_token, id)
      text = message.get("text")
      print("Text: ", text)
      response = api_ai_request(text,roomId)
      #print("Response:",json.dumps(response, indent=4))
      #fulfillment = response.get("fulfillment")
      result = response.get("result")
      action = result.get("action")
      print("Action:", action)
      processRequestSpark(response, roomId)


    return "OK"

######################################################################################################################
#  Natural Language:
#  -  Enviamos peticiones a nuestro agente en Api.ai
#  -
#  -  ...
######################################################################################################################

def api_ai_request(query_from_spark, roomId):

    ai = apiai.ApiAI(api_ai_token)

    request = ai.text_request()

    request.lang = 'es'  # optional, default value equal 'en'

    request.session_id = roomId[-20:]

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
#  Procesamiento de peticiones:
#  -  Desde Api.ai
#  -  Desde una sala de Spark
#  -  ...
######################################################################################################################
def processRequestSpark(req, roomId):
    dato = ""
    # Datos de Acceso del Bot: Token del BOT

    if req.get("result").get("action") == "estadisticas":
        result = req.get("result")
        parameters = result.get("parameters")
        mes = parameters.get("meses")
        tipoInforme = "informe estadisticas"
        worksheet = "Informes"
        dato = leeExcel(mes,tipoInforme, worksheet)
        dato_markdown = "[informe](" + dato + ")"
        status = post_message_markDown(roomId, bot_token, dato_markdown)

    elif req.get("result").get("action") == "Inventario":
        result = req.get("result")
        parameters = result.get("parameters")
        numeroSerie = parameters.get("Serial_Number")
        InformacionEquipo = parameters.get("datos_inventario")
        worksheet = "Inventario"
        dato = leeExcel(numeroSerie,InformacionEquipo, worksheet)
        status = post_message_markDown(roomId, bot_token, dato)

    elif req.get("result").get("action") == "Ayuda":
        result = req.get("result")
        fulfill = result.get("fulfillment")
        texto = fulfill.get("speech")
        status = post_message_markDown(roomId, bot_token,texto)

    else:
        result = req.get("result")
        fulfill = result.get("fulfillment")
        texto = fulfill.get("speech")
        status = post_message_markDown(roomId, bot_token, texto)
        return {}


    return {}


######################################################################################################################
#  Funciones de la aplicación
#  -  Leer excel
#  -  Escribir en una sala
#  -  ...
######################################################################################################################

# Lee informacion de un archivo google sheet en la nube
def leeExcel(datoFila, datoColumna, worksheet):
    # print ("vamos a leer el excel")

    valorBuscado = ""

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-e08df21666bc.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("Base de datos")

    worksheet = wks.worksheet(worksheet)

    print("datoFila:", datoFila)
    print("datoColumna:", datoColumna)

    valor_datoFila = worksheet.find(datoFila)
    valor_datoColumna = worksheet.find(datoColumna)

    row = valor_datoFila.row
    column = valor_datoColumna.col

    # print("row: ",row, "column: ",column)

    valorBuscado = worksheet.cell(row, column).value

    print("valor Buscado: ", valorBuscado)

    return valorBuscado


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

    print("RoomId:", roomid)
    print("Bottoken: ", bot_token)
    print("JSON a mostrar :", markdown)

    header = {'Authorization': "Bearer " + bot_token, 'content-type': 'application/json'}
    payload = {'roomId': roomid, 'markdown':markdown}


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



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
