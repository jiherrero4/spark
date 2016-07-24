
import json
import os
import requests
import sys


createRoom()

def createRoom():
    # Define header used for authentication
    myToken="YzRjYTFiZDktNDcwOS00N2I2LTg5NDYtZjA4YTYwZGQzN2MyMjFmNWI2YzEtYWMx"
    roomTitle="PruebaCreacionSala"
    headers = { "Authorization": "Bearer "+myToken,   "Content-type": "application/json" }
    # Define the action to be taken in the HTTP request
    roomInfo = { "title": roomTitle }
    # Execute HTTP POST request to create the Spark Room
    r = requests.post("https://api.ciscospark.com/v1/rooms",headers=headers, json=roomInfo)
    room = r.json()
    # Print the result of the HTTP POST request
    print(room)