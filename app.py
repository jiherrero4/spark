#!/usr/bin/env python

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
    if req.get("result").get("action") == "creaSala":
        creaSalaSpark()

    elif req.get("result").get("action") == "creaGrupo":
        creaGrupoSpark()

    elif req.get("result").get("action") == "llama":
        llamaSala()

    elif req.get("result").get("action") == "gestionado":
        dato = leeExcel(req)

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

    #emailFile = userlist.txt
    roomTitle = "Ojete"  # second argument
    # Read the email file and save the emails in an list
    #emails = [line.strip() for line in open(emailFile)]
    emails = ["jiherrero@ttrends.es","fsobrino@ttrends.es","pmartin@ttrends.es","jespejo@ttrends.es","jmvarelad@gmail.com"]

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

    result = req.get("result")
    parameters = result.get("parameters")
    cliente = parameters.get("Clientes")

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-e08df21666bc.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("prueba1")

    worksheet = wks.worksheet("gestionados")

    #cliente = worksheet.find("GESTAMP")
    servicio = worksheet.find("S. Gestionado")

    column = cliente.col
    row = servicio.row

    valorBuscado = worksheet.cell(row, column).value

    return valorBuscado

    print(valorBuscado)

def makeWebhookResult(data):

    if data is None:

      speech = "valor no encotrado..."

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
