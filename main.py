import os

from flask import Flask
from py2neo import Graph

from auth import graph_creds
from Models import Person

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = graph_creds()
graph = Graph(host=host, username=username, password=password, secure=True)

@app.route('/')
def hello():
    return 'Hello, Circles!!'

@app.route('/people/<name>/<age>')
def addPerson(name, age):
    p = Person(name, age)
    graph.create(p)
    return "%s added to database!" % name

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
