# view.py
from flask import Blueprint, render_template,request
import os

view_blueprint = Blueprint('view', __name__, template_folder='templates/view')
UPLOAD_FOLDER = './data/'
SPEECH_RESULT_FOLDER = './speechResult/'
SUMIT_FOLDER = './submitFile/'
EMOTION_RESULT_FOLDER = './emotionResult/'


@view_blueprint.route("/", methods=['GET','POST'])
def azure():
    data={}
    file_list=os.listdir(UPLOAD_FOLDER)
    result_list=os.listdir(SPEECH_RESULT_FOLDER)
    start=0
    end = min(len(file_list),10)
    page_number = 1
    if request.method == 'POST':
        page_number = request.json['page_number']
        start = (page_number-1)*10
        end = min(len(file_list),page_number*10)
        
    for i in range(start,end):
        
        data[file_list[i]] = {}
        if(file_list[i].replace('.mp3','') in result_list):
            data[file_list[i]]['status'] = "Finish"
        else:
            data[file_list[i]]['status'] = "NotYet"
    
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*10:page_number*10],file_list_number=len(file_list),currentPage=page_number)
    
    
@view_blueprint.route("/voice")
def voice():
    return render_template('voice.html')