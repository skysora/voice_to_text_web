from web.database import db
import os
import json
import subprocess
from pydub import AudioSegment
from datetime import datetime, timedelta

from hume.models.config import BurstConfig,LanguageConfig,ProsodyConfig
from azure.storage.blob import BlobServiceClient,BlobServiceClient,generate_container_sas,BlobSasPermissions
from hume import HumeBatchClient

UPLOAD_FOLDER = '/web/data/signal/'
SPEECH_RESULT_FOLDER = '/web/data/speechResult/'
SUMIT_FOLDER = '/web/data/submitFile/'
EMOTION_RESULT_FOLDER = '/web/data/emotionResult/'
PROCESS_SPEECH_RESULT_FOLDER = '/web/data/process_speechResult/'
TEXT_OUTPUT = '/web/data/output/'
TOKEN_PATH="/web/token.json"





def check_exitst_path(file):
    
    file_name = f'{file.title}'
    #singal
    file.singal_file_path = f"{UPLOAD_FOLDER}{file_name}"
    
    #submit
    if os.path.exists(f"{SUMIT_FOLDER}{file_name}.json"):
        file.submit_text_file_path = f"{SUMIT_FOLDER}{file_name}.json"

    #speech
    if os.path.exists(f"{SPEECH_RESULT_FOLDER}{file_name}.json"):
        file.origin_text_file_path = f"{SPEECH_RESULT_FOLDER}{file_name}.json"

    #process_speech_result
    if os.path.exists(f"{PROCESS_SPEECH_RESULT_FOLDER}{file_name}"):
        file.process_speech_file_path = f"{PROCESS_SPEECH_RESULT_FOLDER}{file_name}"

    #text
    if os.path.exists(f"{TEXT_OUTPUT}{file_name}.txt"):
        file.modified_text_file_path = f"{TEXT_OUTPUT}{file_name}.txt"

    #emotion
    if os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}'):
        file.origin_emotion_file_path = f'{EMOTION_RESULT_FOLDER}{file_name}'
        
    db.session.commit()
    
    return file
    
def check_exitst_answer(file,data):
    
    file_name = f'{file.title}'
    # {'result':{'submit':False,"speech":False,"process_speech":False','text':False,emotion':False},'datetime':''}
    
    #submit
    if (os.path.exists(f'{file.submit_text_file_path}')):
        data[file_name]['result']["submit"] = True
        
    #speech
    if (os.path.exists(f'{file.origin_text_file_path}')):
        data[file_name]['result']["speech"] = True
        
    #process_speech        
    audio_path = f'{file.process_speech_file_path}/audio/'
    text_path = f'{file.process_speech_file_path}/text/'
    if(os.path.exists(audio_path)):
        if (len(os.listdir(audio_path)) == len(os.listdir(text_path)) and os.listdir(text_path)!=0):
            data[file_name]['result']["process_speech"] = True
        
    #text
    if (os.path.exists(f'{file.modified_text_file_path}')):
        data[file_name]['result']["text"] = True
        
    #emotion
    if (os.path.exists(f'{file.origin_emotion_file_path}')):
        data[file_name]['result']["emotion"] = True
        
    return data

def check_submit_speech(file_name):
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
            subprocess.run(f'wget -O "{SPEECH_RESULT_FOLDER}{file_name}.json" "{answer_path}"', shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            pass
    else:
        # error
        print(result.stderr)
        
def generate_process_speech_result(origin_text_file_path,singal_file_path,process_speech_file_path):
    
    #創建前處理資料夾
    if not os.path.exists(f'{process_speech_file_path}'):
        os.makedirs(f'{process_speech_file_path}/audio/')
        os.makedirs(f'{process_speech_file_path}/text/')
        
    with open(origin_text_file_path) as file_text:
        text_data = json.load(file_text)
        
    audio = AudioSegment.from_file(singal_file_path, format="mp3")
    count = 0
    for phrases in text_data['recognizedPhrases']:
        if(phrases['channel']!=0):
            continue
        start_time = float(phrases['offsetInTicks'])/10000
        end_time  = start_time + float(phrases['durationInTicks'])/10000
        # 切出特定时间段的音频
        segment = audio[start_time:end_time]
        segment.export(f"{process_speech_file_path}/audio/{count}.mp3", format="mp3")
        with open(f"{process_speech_file_path}/text/{count}.txt",'w') as text:
            text.write(phrases['nBest'][0]['display'])
            
        count +=1
        

def emotion_identify(file_title,process_speech_file_path):
    
    
    with open(f'{TOKEN_PATH}', 'r') as test:
        data = json.load(test)
        
    # Usage example
    blob_service_client = BlobServiceClient.from_connection_string(data['blob_service_client_string'])
    container_name = 'ntustvoice'
    folder_to_upload = f"{process_speech_file_path}/audio"
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
  
def emotion_identify_one(client,folder_name,file_name,urls,):
    
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
                            
def ConvertUTF8(path):
    # Opening JSON file
    with open(path, 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
        
    with open(path, "w") as outfile:
        json.dump(json_object, outfile,ensure_ascii=False) 