#!/usr/bin/env python

import urllib
import json
import os
import requests
import sys

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

    print("Request:")

    # Con indent lo que hacemos es introducir espacios en el formato de salida
    # de forma que se lea mejor, no simplemente un texto plano.
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    # Transformo res a un formato json tabulado.
    res = json.dumps(res, indent=4)
    # print(res)
    # La respuesta tiene que ser tipo application/json
    # La función make_response pertenece a la libreria de Flask
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

# En esta función vamos a procesar el mensaje que hemos recibido, webhook (post).
# Lo primero que vamos a buscar es la acción a realizar.
#
#
def processRequest(req):
    if req.get("result").get("action") != "creaSala":
        return {}

    myToken = "YzRjYTFiZDktNDcwOS00N2I2LTg5NDYtZjA4YTYwZGQzN2MyMjFmNWI2YzEtYWMx"
    roomTitle = "PruebaCreacionSala"
    headers = {"Authorization": "Bearer " + myToken, "Content-type": "application/json"}
    # Define the action to be taken in the HTTP request
    roomInfo = {"title": roomTitle}
    # Execute HTTP POST request to create the Spark Room
    r = requests.post("https://api.ciscospark.com/v1/rooms", headers=headers, json=roomInfo)
    room = r.json()
    res = makeWebhookResult()
    return res

def makeWebhookResult():

    speech = "Sala creada, y prueba superada"

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "from spark"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
