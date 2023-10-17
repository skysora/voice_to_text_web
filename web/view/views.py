# view.py
from flask import Blueprint, render_template,request,redirect,url_for
import os
import pytz
import json
import subprocess
from flask import Blueprint, request,render_template
from flask_login import current_user
from web.models.models import File

view_blueprint = Blueprint('view', __name__, template_folder='templates/view')

UPLOAD_FOLDER = './data/signal/'
SPEECH_RESULT_FOLDER = './data/speechResult/'
SUMIT_FOLDER = './data/submitFile/'
EMOTION_RESULT_FOLDER = './data/emotionResult/'



@view_blueprint.route("/main", methods=['GET','POST'])
def azure():
    
    page_limit = 10
    user_files = File.query.filter_by(user_id=current_user.id).all()
    file_list=[file.title for file in user_files]
    start=0
    end = min(len(user_files),page_limit)
    page_number = 1
    if request.method == 'POST':
        page_number = request.json['page_number']
        start = (page_number-1)*page_limit
        end = min(len(user_files),page_number*page_limit)
    
    
    data={}
    with open('./web/test.txt','w') as test:
        test.write(f"start:{start},end:{end}")
        
    for file in user_files[start:end]:
        
        file_name = f'{file.title}'
        data[file_name] = {'result':{'speech':False,'emotion':True},'datetime':'','User':f'{current_user.username}'}
        data[file_name]['datetime'] = f'{file.timestamp}'
        #speech 
        if os.path.exists(f'{file.origin_text_file_path}'):
            data[file_name]['result']['speech'] = True
        else:
            if os.path.exists(f'{file.submit_text_file_path}'):
                check_speech(file_name)
                if os.path.exists(f'{file.origin_text_file_path}'):
                    data[file_name]['result']['speech'] = True
        #emotion 
        for emotion_file in [f'{file.origin_emotion_file_path}/burst.json', f'{file.origin_emotion_file_path}/prosody.json', f'{file.origin_emotion_file_path}/language.json']:
            if not os.path.exists(f'{emotion_file}'):
                data[file_name]['result']['emotion'] = False
                break
            else:
                data[file_name]['result']['emotion'] = True
        
        if(data[file_name]['result']['speech'] and data[file_name]['result']['emotion']):
            data[file_name]['status'] = "Finish"
        elif(not data[file_name]['result']['emotion'] and os.path.exists(f'{file.origin_emotion_file_path}')):
            data[file_name]['status'] = "Waiting" 
        else:
            data[file_name]['status'] = "NotYet"
            
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*page_limit:page_number*page_limit],file_list_number=len(user_files),currentPage=page_number)
    
    
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