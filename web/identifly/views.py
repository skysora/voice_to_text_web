# identifly.py
from flask import Blueprint,Flask, request, redirect, url_for,render_template,send_file, jsonify
import os
import json
from azure.storage.blob import BlobServiceClient,BlobServiceClient,generate_container_sas,BlobSasPermissions
import subprocess
from hume import HumeBatchClient
from datetime import datetime, timedelta
from hume.models.config import BurstConfig,LanguageConfig,ProsodyConfig
import shutil
import threading


identifly_blueprint = Blueprint('identifly', __name__, template_folder='templates')
UPLOAD_FOLDER = './data/signal/'
SPEECH_RESULT_FOLDER = './data/speechResult/'
SUMIT_FOLDER = './data/submitFile/'
EMOTION_RESULT_FOLDER = './data/emotionResult/'



@identifly_blueprint.route('/upload_file', methods=['POST'])
def upload_file():
    # Iterate for each file in the files List, and Save them
    files = request.files.getlist('files[]')
    for file in files:
        # 本地端測試
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return redirect(url_for('view.azure'))
      
@identifly_blueprint.route('/download_file', methods=['get'])
def download_file():
    file_name = request.args.get('name')
    return send_file(f'{UPLOAD_FOLDER}{file_name}',as_attachment=True)


@identifly_blueprint.route('/delete_file', methods=['get'])
def delete_file():
    file_name = request.args.get('name')
    os.remove(f'{UPLOAD_FOLDER}{file_name}')
    return redirect(url_for('view.azure'))


@identifly_blueprint.route('/insert_file_idenitfy', methods=['get'])
def insert_file_idenitfy():
    file_name = request.args.get('name')
    
    with open('token.json', 'r') as file:
        data = json.load(file)
        
    command  = f'/root/.dotnet/tools/spx config @key --set {data["voiceKey"]}'
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    command  = f'/root/.dotnet/tools/spx config @region --set {data["voiceLocation"]}'
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # upload file to cloud
    blob_service_client = BlobServiceClient.from_connection_string(data['blob_service_client_string'])
    upload_file_path = os.path.join(UPLOAD_FOLDER, file_name)
    blob_client = blob_service_client.get_blob_client(container='ntustvoice', blob=file_name)
    # Upload the created file
    try:
        with open(file=upload_file_path, mode="rb") as data:
            blob_client.upload_blob(data)
    except:
        pass
    
    
    # SPEECH IDENTIFY
    submit_list=os.listdir(SUMIT_FOLDER)
    if(f'{file_name}.json' not in submit_list):
        speech_idenitfy(file_name)
        
    task_thread = threading.Thread(target=emotion_identify,args=((file_name,)))
    task_thread.start()
    
    return redirect(url_for('view.azure'))

def ConvertUTF8(path):
    # Opening JSON file
    with open(path, 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
        
    with open(path, "w") as outfile:
        json.dump(json_object, outfile,ensure_ascii=False) 
        
def speech_idenitfy(file_name):
    command  = f'/root/.dotnet/tools/spx batch transcription create --language "zh-CN" --name "{file_name}" --content "https://ntuststorage2.blob.core.windows.net/ntustvoice/{file_name}"'
    
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open('example.txt', 'a') as file:
        file.write(f'{command}\n')
    # 检查是否有错误输出
    if result.returncode == 0:
        # 命令成功执行
        print("命令执行成功：")
        data = result.stdout.split('\n')
        result_str = "\n".join(data[14:])
        out = json.loads(result_str)
        with open(f'{SUMIT_FOLDER}{out["displayName"]}.json', "w") as json_file:
            json.dump(out, json_file)
    else:
        # 命令执行失败，输出错误信息
        print("命令执行失败：")
        

def emotion_identify(file_name):
    
    file_name = file_name
    print(file_name)
    with open('token.json', 'r') as file:
        data = json.load(file)
        
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
    # 构建 SAS URL
    urls = [f"https://{blob_name}.blob.core.windows.net/{container_name}/{file_name}?{sas_token}"]

    client = HumeBatchClient(data['humeKey'])
    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}'):
        os.mkdir(f'{EMOTION_RESULT_FOLDER}{file_name}')

    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}/burst.json'):
        job = client.submit_job(urls, [BurstConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/burst.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/burst.json')

    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}/prosody.json'):
        job = client.submit_job(urls, [ProsodyConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/prosody.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/prosody.json')

    if not os.path.exists(f'{EMOTION_RESULT_FOLDER}{file_name}/language.json'):
        job = client.submit_job(urls, [BurstConfig()])
        job.await_complete()
        job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/language.json')
        ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/language.json')

    
@identifly_blueprint.route('/speech_idenitfy_download', methods=['get'])
def speech_idenitfy_download():
    
    file_name = request.args.get('name')
        
    result_list=os.listdir(SPEECH_RESULT_FOLDER)
    submit_list=os.listdir(SUMIT_FOLDER)
    if(f'{file_name}.json' not in result_list):
        if(f'{file_name}.json' not in submit_list):
            return redirect(url_for('azure'))
    
    return send_file(f'{SPEECH_RESULT_FOLDER}{file_name}.json',as_attachment=True)


@identifly_blueprint.route('/emotion_idenitfy_download', methods=['get'])
def emotion_idenitfy_download():
    file_name = request.args.get('name')
    emotion_result_list=os.listdir(EMOTION_RESULT_FOLDER)
    if(f'{file_name}' not in emotion_result_list):
        return redirect(url_for('azure'))
    else:
        if(f'{file_name}.zip' not in emotion_result_list):
            shutil.make_archive(f'{EMOTION_RESULT_FOLDER}{file_name}', 'zip', f'{EMOTION_RESULT_FOLDER}{file_name}')
        
        
    return send_file(f'{EMOTION_RESULT_FOLDER}{file_name}.zip',as_attachment=True)
    
    