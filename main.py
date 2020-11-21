# way to upload image: endpoint
# way to save the image
# function to make prediction on the image
# show the results
import os
from flask import Flask
from flask import request
from flask import render_template
import cv2
import numpy as np
from keras.models import Model, load_model
from pymongo import MongoClient
import base64
import datetime
import socket
from datetime import date, timedelta


app = Flask(__name__)
UPLOAD_FOLDER = "static"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DEVICE = "cpu"
MODEL = None
HOST = '127.0.0.1'
PORT = 8082


def predict(image_path, model):
    I = []
    print(image_path)
    img=cv2.imread(image_path)
    img=cv2.resize(img,(100,100))
    img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    I.append(img)
    NP_ARRAY = np.array(I)
    X_VAL = NP_ARRAY/255.0
    R = MODEL.predict_classes(X_VAL)
    #model.predict(X_VAL) > 0.5).astype("int32")

    
    LABEL=''

    if(R[0]==0):
        LABEL = 'BOA SEM MANCHAS'
    if(R[0]==1):
        LABEL = 'RUIM'
    if(R[0]==2):
        LABEL = 'BOA COM MANCHAS'

    # Cria um objeto socket
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     # Conecta ao servidor
    #     s.connect((HOST, PORT))
    #     # Envia a mensagem - LABEL ('BOA COM MANCHAS', 'BOA SEM MANCHAS', 'RUIM')
    #     s.sendall(str.encode(LABEL))
    #     # Lê a resposta do servidor
    #     data = s.recv(1024)

    connect_and_save_mongo(LABEL, img)

    return LABEL
    
def connect_and_save_mongo(classification, img):
    
    print('conectando mongo')
    #Conecta mongo local
    logs_prod    = MongoClient('mongodb://admin:admin@localhost:27017/local?authSource=admin')
    cliente_prod = MongoClient('mongodb://admin:admin@localhost:27017/orange_classification?authSource=admin')
        
    db_logs   = logs_prod.local
    db_prod   = cliente_prod.orange_classification

    coll_logs = db_logs.startup_log
    coll_prod = db_prod.oranges

    print(coll_logs)
    actual_connection = coll_logs.find({}).sort('_id', -1).limit(1)
    for x in actual_connection:
        batch = x['_id']

    mydict = { "classification": classification, "image":base64.b64encode(img), 'batch': batch, 'date': datetime.datetime.now() }
    coll_prod.insert(mydict)
    print('insert realizado')
    
    #Manda p/ eletronica

    #Salva mongo

    #Faz o reduce dos resultados (pega varias fotos da mesma laranja e retorna um resultado)   


@app.route("/", methods=["GET", "POST"])
def upload_predict():
    
    teste = []
    if request.method == "POST":
        image_file = request.files.getlist("image")
        
        PRED = []
        for image in image_file:

            if image:
                image_location = os.path.join(
                    UPLOAD_FOLDER,
                    image.filename
                )
                image.save(image_location)
                pred = predict(image_location, MODEL)
                PRED.append(pred)
                teste.append({'url': './static/'+image.filename, 'label': pred})
    #return render_template("index.html", prediction=0, image_loc=None)

    FINAL = ''
    #if(PRED[0]==PRED[1]):
    #    FINAL = PRED[0]

    return render_template("index.html", image_locs=teste)


if __name__ == "__main__":
    
    MODEL=load_model('./h5/rottenvsfresh.h5')
    
    app.run(host='0.0.0.0', port='5000', debug=True)
