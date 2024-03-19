from flask import Flask, render_template,jsonify, request
app = Flask(__name__)

import requests


from pymongo import MongoClient
client = MongoClient('mongodb://test:test@localhost',27017) #원격 DB접속
#client = MongoClient('localhost',27017)
db = client.dbjungle

##URL 별로 함수명이 같거나,
## route('/') 등의 주소가 같으면 안됨.


@app.route('/main')
def main():
    return render_template('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug = True)
