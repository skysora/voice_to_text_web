# view.py
from flask import Blueprint, render_template,request,redirect,url_for
import os
import pytz
import json
import subprocess
from flask import Blueprint, request,render_template
from flask_login import current_user
from web.models.models import File
from web.database import db
from pydub import AudioSegment
import threading

view_blueprint = Blueprint('view', __name__, template_folder='templates/view')

UPLOAD_FOLDER = '/web/data/signal/'
SPEECH_RESULT_FOLDER = '/web/data/speechResult/'
SUMIT_FOLDER = '/web/data/submitFile/'
EMOTION_RESULT_FOLDER = '/web/data/emotionResult/'
PROCESS_SPEECH_RESULT_FOLDER = '/web/data/process_speechResult/'



@view_blueprint.route("/main", methods=['GET','POST'])
def azure():
    
    page_limit = 10
    user_files = File.query.filter_by(user_id=current_user.id).order_by(File.timestamp.desc()).all()
    
    file_list=[file.title for file in user_files]
    
    start=0
    end = min(len(user_files),page_limit)
    page_number = 1
    if request.method == 'POST':
        page_number = request.json['page_number']
        start = (page_number-1)*page_limit
        end = min(len(user_files),page_number*page_limit)
    
    
    data={}
    for file in user_files[start:end]:
        
        file_name = f'{file.title}'
        data[file_name] = {'result':{'speech':False,'emotion':True,'edit':True},'datetime':'','User':f'{current_user.username}'}
        data[file_name]['datetime'] = f'{file.timestamp}'
        # 檢查這個檔案的答案是不是已經在資料夾內
        check_exitst_answer(file)
        
        #speech 
        if os.path.exists(f'{file.origin_text_file_path}'):
            data[file_name]['result']['speech'] = True
        else:
            if os.path.exists(f'{file.submit_text_file_path}'):
                
                check_speech(file_name)
        
        
        #process_speech_result
        if os.path.exists(f'{file.origin_text_file_path}'):
            data[file_name]['result']['speech'] = True
            if (file.modified_text_file_path == None or (not os.path.exists(file.modified_text_file_path))):
                file.modified_text_file_path = f'{PROCESS_SPEECH_RESULT_FOLDER}{file_name}'
                db.session.commit()
                with open ("./web/test.txt",'w') as text:
                    text.write(f"123:{file.modified_text_file_path}")
                task_thread = threading.Thread(target=generate_process_speech_result,args=((file.title,file.origin_text_file_path,file.file_path,file.modified_text_file_path)))
                task_thread.start()
                    
        #emotion 
        for emotion_file in [f'{file.origin_emotion_file_path}/burst.json', f'{file.origin_emotion_file_path}/prosody.json', f'{file.origin_emotion_file_path}/language.json']:
            if not os.path.exists(f'{emotion_file}'):
                data[file_name]['result']['emotion'] = False
                break
            else:
                data[file_name]['result']['emotion'] = True
            
        check_emotion(file_name,data[file_name]['result']['emotion'])
        
        audio_path = f'{file.modified_text_file_path}/audio/'
        text_path = f'{file.modified_text_file_path}/text/'
        
        if  (not os.path.exists(file.modified_text_file_path)) or (len(os.listdir(audio_path)) != len(os.listdir(text_path))):
            data[file_name]['result']['edit'] = False
    
        #判斷狀態
        if(data[file_name]['result']['speech'] and data[file_name]['result']['emotion'] and data[file_name]['result']['edit']):
            data[file_name]['status'] = "Finish"
        elif(not data[file_name]['result']['emotion'] and os.path.exists(f'{file.origin_emotion_file_path}')):
            data[file_name]['status'] = "Waiting" 
        else:
            data[file_name]['status'] = "NotYet"
            
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*page_limit:page_number*page_limit],file_list_number=len(user_files),currentPage=page_number)
    
    
@view_blueprint.route("/voice")
def voice():
    return render_template('voice.html')


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
            file = File.query.filter_by(title=file_name).first()
            file.submit_text_file_path = f'{SPEECH_RESULT_FOLDER}{file_name}.json'
            db.session.commit()
        except:
            pass
    else:
        # error
        print(result.stderr)
        
def generate_process_speech_result(filename,text_path,audio_file_path,modified_text_file_path):
    
        
    with open(text_path) as file_text:
        text_data = json.load(file_text)
        
    audio = AudioSegment.from_file(audio_file_path, format="mp3")
    
    
    if not os.path.exists(f'{modified_text_file_path}'):
        os.makedirs(f'{modified_text_file_path}/audio/')
        os.makedirs(f'{modified_text_file_path}/text/')
        
    count = 0
    for phrases in text_data['recognizedPhrases']:
        start_time = float(phrases['offsetInTicks'])/10000
        end_time  = start_time + float(phrases['durationInTicks'])/10000
        # 切出特定时间段的音频
        segment = audio[start_time:end_time]
        segment.export(f"{modified_text_file_path}/audio/{count}.mp3", format="mp3")
        with open(f"{modified_text_file_path}/text/{count}.txt",'w') as text:
            text.write(phrases['nBest'][0]['display'])
            
        count +=1

        
def check_exitst_answer(file):
    
    file_name = f'{file.title}'
    
    
    if os.path.exists(f'{SPEECH_RESULT_FOLDER}{file_name}.json'):
        file.submit_text_file_path = f"{SUMIT_FOLDER}{file_name}.json"
        file.origin_text_file_path = f"{SPEECH_RESULT_FOLDER}{file_name}.json"
    
    if os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}'): 
        file.origin_emotion_file_path = f'{EMOTION_RESULT_FOLDER}{file_name}'
        
    db.session.commit()
    
def check_emotion(file_name,flag):
    if flag:
        file = File.query.filter_by(title=file_name).first()
        file.origin_emotion_file_path = f'{EMOTION_RESULT_FOLDER}{file_name}'
        db.session.commit()