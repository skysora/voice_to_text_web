# view.py
from flask import Blueprint, render_template,request
import os
import json
import subprocess
from flask_login import current_user
from web.models.models import File
from web.database import db
from pydub import AudioSegment
import threading
from azure.storage.blob import BlobServiceClient,BlobServiceClient,generate_container_sas,BlobSasPermissions
from hume import HumeBatchClient
from datetime import datetime, timedelta
from hume.models.config import BurstConfig,LanguageConfig,ProsodyConfig
from web.models.models import User,UserRoleEnum


view_blueprint = Blueprint('view', __name__, template_folder='templates/view')
UPLOAD_FOLDER = '/web/data/signal/'
SPEECH_RESULT_FOLDER = '/web/data/speechResult/'
SUMIT_FOLDER = '/web/data/submitFile/'
EMOTION_RESULT_FOLDER = '/web/data/emotionResult/'
PROCESS_SPEECH_RESULT_FOLDER = '/web/data/process_speechResult/'
TEXT_OUTPUT = '/web/data/output/'
TOKEN_PATH="/web/token.json"



@view_blueprint.route("/main", methods=['GET','POST'])
def azure():
    
    page_limit = 10
    all_users=None
    user = User.query.filter_by(id=current_user.id).first()
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
    
    if request.method == 'POST':
        select_user_id = request.json['select_user_id']
        
    else:
        select_user_id = current_user.id
        
    select_user_flag = int(select_user_id)==int(current_user.id)
    user_files = File.query.filter_by(user_id=select_user_id).order_by(File.timestamp.desc()).all()
    file_list=[file.title for file in user_files]
    
    start=0
    end = min(len(user_files),page_limit)
    page_number = 1
    if request.method == 'POST':
        page_number = int(request.json['page_number'])
        if page_number>1:
            start = (page_number-1)*page_limit
            end = min(len(user_files),page_number*page_limit)
    

    data={}
    for file in user_files[start:end]:
        
        file_name = f'{file.title}'
        data[file_name] = {'result':{'speech':False,"submit":False,'emotion':False,'edit':False,'text':False},'datetime':'','User':f'{User.query.filter_by(id=file.user_id).first().username}'}
        data[file_name]['datetime'] = f'{file.timestamp}'
        # 檢查這個檔案的答案是不是已經在資料夾內
        check_exitst_answer(file)
        

        if (os.path.exists(f'{file.submit_text_file_path}')):
            data[file_name]['result']["submit"] = True

        #speech 
        if (not os.path.exists(f'{file.origin_text_file_path}')) and (os.path.exists(f'{file.submit_text_file_path}')):
            check_speech(file_name)
            
        #process_speech_result
        if os.path.exists(f'{file.origin_text_file_path}') and os.path.exists(f'{file.submit_text_file_path}'):
            data[file_name]['result']['speech'] = True
            file.modified_text_file_path = f'{PROCESS_SPEECH_RESULT_FOLDER}{file_name}'
            db.session.commit()
            if ((not os.path.exists(file.modified_text_file_path))):
                task_thread = threading.Thread(target=generate_process_speech_result,args=((file.title,file.origin_text_file_path,file.file_path,file.modified_text_file_path)))
                task_thread.start()
           

        audio_path = f'{file.modified_text_file_path}/audio/'
        text_path = f'{file.modified_text_file_path}/text/'
        # 產生情緒辨識檔案
        try:
            if (file.modified_text_file_path != None) and (len(os.listdir(audio_path)) == len(os.listdir(text_path))):
                if os.path.exists(file.modified_text_file_path) and (file.origin_emotion_file_path == None or not os.path.exists(file.origin_emotion_file_path) or len(os.listdir(file.origin_emotion_file_path))!=len(os.listdir(text_path))):
                    file.origin_emotion_file_path = f'{EMOTION_RESULT_FOLDER}{file.title}'
                    db.session.commit()
                    # emotion_identify(file)
                    task_thread = threading.Thread(target=emotion_identify,args=((file.title,file.modified_text_file_path)))
                    task_thread.start()
        except:
            pass

    
        
        #情緒辨識結果
        if(file.origin_emotion_file_path != None):
            try:
                if(len(os.listdir(file.origin_emotion_file_path)) == len(os.listdir(text_path))):
                    data[file_name]['result']['emotion'] = True
            except:
                pass
            
        try:
            if(len(os.listdir(audio_path)) == len(os.listdir(text_path)) and (int(select_user_id)==int(current_user.id))):
                data[file_name]['result']['edit'] = True
        except:
            pass
            
        if(os.path.exists(f'{TEXT_OUTPUT}{file_name}.txt')):
            data[file_name]['result']['text'] = True
            
        #判斷狀態
        if(data[file_name]['result']['emotion'] and data[file_name]['result']['speech'] and data[file_name]['result']['text']):
            data[file_name]['status'] = "Finish"
        
        elif(not data[file_name]['result']['emotion'] and not data[file_name]['result']['speech'] and not data[file_name]['result']['text']):
            data[file_name]['status'] = "NotYet"
            
        elif(not data[file_name]['result']["submit"]):
            data[file_name]['status'] = "Speech Waiting"
        elif(not data[file_name]['result']['text']):
            data[file_name]['status'] = "Text Waiting"
        elif(not data[file_name]['result']['emotion']):
            data[file_name]['status'] = "Emototion Waiting" 
            
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*page_limit:page_number*page_limit],
                           file_list_number=len(user_files),currentPage=page_number,user_list = all_users,
                           select_user_id = select_user_id,select_user_flag = select_user_flag,
                           )
    
    
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
    
def upload_folder_contents(blob_service_client, container_name, folder_path,folder_name):
    # List all files in the folder and its subfolders
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            # Create the BlobClient for each file
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=f"{folder_name}/{file_name}")

            # Check if the blob (file) already exists in the container
            if not blob_client.exists():
                try:
                    # Upload the file
                    with open(os.path.join(root, file_name), mode="rb") as data:
                        blob_client.upload_blob(data)
                except Exception as error:
                    pass
            
def emotion_identify_one(client,folder_name,file_name,urls):
    
    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/'):
        # 如果不存在，建立檔案夾
        os.makedirs(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/')
    
    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/burst.json'):
        job = client.submit_job(urls, [BurstConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/burst.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/burst.json')

    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/prosody.json'):
        job = client.submit_job(urls, [ProsodyConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/prosody.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/prosody.json')

    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/language.json'):
        job = client.submit_job(urls, [LanguageConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/language.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{folder_name}/{file_name}/language.json')
    
def emotion_identify(file_title,modified_text_file_path):
    
    
    with open(f'{TOKEN_PATH}', 'r') as test:
        data = json.load(test)
        
    # Usage example
    blob_service_client = BlobServiceClient.from_connection_string(data['blob_service_client_string'])
    container_name = 'ntustvoice'
    folder_to_upload = f"{modified_text_file_path}/audio"
    upload_folder_contents(blob_service_client, container_name, folder_to_upload,file_title)
    
        
    # 导入存储连接字符串和容器名称
    blob_storage_key = data['blob_storage_key']
    container_name = "ntustvoice"
    blob_name = "ntuststorage2"  # 文件名称

    # 设置 SAS 的权限
    permissions = BlobSasPermissions(read=True)  # 可以根据需要调整权限

    # # 生成 Blob 的 SAS
    sas_token = generate_container_sas(
            account_name=blob_name,
            container_name=container_name,
            account_key=blob_storage_key,
            permission=permissions,
            expiry=  datetime.now()+ timedelta(days=1)
    )
    client = HumeBatchClient(data['humeKey'])
    for _, _, files in os.walk(folder_to_upload):
        for file_name in files:
            # Create the BlobClient for each file
            urls = [f"https://{blob_name}.blob.core.windows.net/{container_name}/{file_title}/{file_name}?{sas_token}"]
            emotion_identify_one(client,file_title,file_name,urls)

def ConvertUTF8(path):
    # Opening JSON file
    with open(path, 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
        
    with open(path, "w") as outfile:
        json.dump(json_object, outfile,ensure_ascii=False) 
    