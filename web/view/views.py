# view.py
from flask import Blueprint, render_template,request
import os
from datetime import datetime
import pytz
import json
import subprocess
from flask import Blueprint,Flask, request, redirect, url_for,render_template,send_file, jsonify
import time
import threading

view_blueprint = Blueprint('view', __name__, template_folder='templates/view')
UPLOAD_FOLDER = './data/signal/'
SPEECH_RESULT_FOLDER = './data/speechResult/'
SUMIT_FOLDER = './data/submitFile/'
EMOTION_RESULT_FOLDER = './data/emotionResult/'



@view_blueprint.route("/main", methods=['GET','POST'])
def azure():
    data={}
    file_list=os.listdir(UPLOAD_FOLDER)
    result_list=os.listdir(SPEECH_RESULT_FOLDER)
    sumit_result_list=os.listdir(SUMIT_FOLDER)
    start=0
    end = min(len(file_list),10)
    page_number = 1
    if request.method == 'POST':
        page_number = request.json['page_number']
        start = (page_number-1)*10
        end = min(len(file_list),page_number*10)
        
    for i in range(start,end):
        file_name = file_list[i]
        data[file_name] = {'result':{'speech':False,'emotion':True}}
        #speech 
        if os.path.exists(f'{SPEECH_RESULT_FOLDER}/{file_name}.json'):
            data[file_name]['result']['speech'] = True
        else:
            if(f'{file_name}.json' in sumit_result_list):
                check_speech(file_name)
                if os.path.exists(f'{SPEECH_RESULT_FOLDER}/{file_name}.json'):
                    data[file_name]['result']['speech'] = True
        #emotion 
        for file in [f'{EMOTION_RESULT_FOLDER}/{file_name}/burst.json', f'{EMOTION_RESULT_FOLDER}/{file_name}/prosody.json', f'{EMOTION_RESULT_FOLDER}/{file_name}/language.json']:
            if not os.path.exists(f'{file}'):
                data[file_name]['result']['emotion'] = False
                break
            else:
                data[file_name]['result']['emotion'] = True
        
        
        #time
        ctime_timestamp = os.path.getctime(f'{UPLOAD_FOLDER}/{file_name}')
        ctime_datetime = datetime.fromtimestamp(ctime_timestamp)
        ctime_datetime_tz = ctime_datetime.astimezone(pytz.timezone('Asia/Taipei'))
        data[file_name]['datetime'] = ctime_datetime_tz.strftime('%Y-%m-%d %H:%M:%S')
        
        
        if(data[file_name]['result']['speech'] and data[file_name]['result']['emotion']):
            data[file_name]['status'] = "Finish"
        elif(not data[file_name]['result']['emotion'] and os.path.exists(f'{EMOTION_RESULT_FOLDER}/{file_name}')):
            data[file_name]['status'] = "Waiting" 
        else:
            data[file_name]['status'] = "NotYet"
            
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*10:page_number*10],file_list_number=len(file_list),currentPage=page_number)
    
    
@view_blueprint.route("/voice")
def voice():
    return render_template('voice.html')


@view_blueprint.route('/popup')
def popup():
    return render_template('popup.html')


def check_speech(file_name):
    f = open(f'{SUMIT_FOLDER}{file_name}.json')
    data = json.load(f)
    f.close()
    id = data['links']['files'].split('/')[-2]
    
    command  = f'/root/.dotnet/tools/spx batch transcription list --api-version v3.1 --files --transcription {id}'
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # 检查是否有错误输出
    if result.returncode == 0:
        # sucuss
        result_str = "\n".join(result.stdout.split('\n')[14:])
        out = json.loads(result_str)
        
        try:
            answer_path = out['values'][0]['links']['contentUrl']
            answer = subprocess.run(f'wget -O "{SPEECH_RESULT_FOLDER}{file_name}.json" "{answer_path}"', shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            pass
    else:
        # error
        with open("test.txt") as file:
            file.write(f'{result.stderr}\n')
        print(result.stderr)