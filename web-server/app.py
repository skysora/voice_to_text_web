
from flask import Flask, request, redirect, url_for,render_template,send_file, jsonify
import os
import time
import os
import subprocess
import json
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient,BlobServiceClient,generate_container_sas,BlobSasPermissions
from hume import HumeBatchClient
from hume.models.config import BurstConfig,LanguageConfig,ProsodyConfig

from datetime import datetime, timedelta
import shutil


app = Flask(__name__)
app.debug = True
UPLOAD_FOLDER = './data/'
SPEECH_RESULT_FOLDER = './speechResult/'
SUMIT_FOLDER = './submitFile/'
EMOTION_RESULT_FOLDER = './emotionResult/'


@app.route("/", methods=['GET','POST'])
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
    
    with open('output.txt', 'w') as file:
        # 写入内容到文件
        file.write(f'start:{start}\n')
        file.write(f'end:{end}\n')
        
    for i in range(start,end):
        
        data[file_list[i]] = {}
        if(file_list[i].replace('.mp3','') in result_list):
            data[file_list[i]]['status'] = "Finish"
        else:
            data[file_list[i]]['status'] = "NotYet"
            
    return render_template('azure.html',data=data,file_list = file_list[(page_number-1)*10:page_number*10],file_list_number=len(file_list),currentPage=page_number)
    

@app.route("/voice")
def voice():
    return render_template('voice.html')



@app.route('/upload_file', methods=['POST'])
def upload_file():
    # Iterate for each file in the files List, and Save them
    files = request.files.getlist('files[]')
    for file in files:
        # 本地端測試
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return redirect(url_for('azure'))
    
@app.route('/download_file', methods=['get'])
def download_file():
    file_name = request.args.get('name')
    return send_file(f'{UPLOAD_FOLDER}{file_name}',as_attachment=True)


@app.route('/delete_file', methods=['get'])
def delete_file():
    file_name = request.args.get('name')
    os.remove(f'{UPLOAD_FOLDER}{file_name}')
    return redirect(url_for('azure'))


@app.route('/insert_file_idenitfy', methods=['get'])
def insert_file_idenitfy():
    file_name = request.args.get('name')
    
    with open('token.json', 'r') as file:
        data = json.load(file)
        
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
    
    
    # # SPEECH IDENTIFY
    submit_list=os.listdir(SUMIT_FOLDER)
    if(f'{file_name}.json' in submit_list):
        return redirect(url_for('azure'))
    else:
        speech_idenitfy(file_name)
        
    # EMOTION IDENTIFY
    emotion_result_list=os.listdir(EMOTION_RESULT_FOLDER)
    if(f'{file_name}' in emotion_result_list):
        return redirect(url_for('azure'))
    else:
        emotion_identify(file_name)
        
    return redirect(url_for('azure'))

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
        print(result.stderr)

def emotion_identify(file_name):
    
    
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
    
    os.mkdir(f'{EMOTION_RESULT_FOLDER}{file_name}')

    job = client.submit_job(urls, [BurstConfig()])
    details = job.await_complete()
    job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/burst.json')
    ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/burst.json')


    job = client.submit_job(urls, [ProsodyConfig()])
    job.await_complete()
    job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/prosody.json')
    ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/prosody.json')


    job = client.submit_job(urls, [BurstConfig()])
    job.await_complete()
    job.download_predictions(f'{EMOTION_RESULT_FOLDER}{file_name}/language.json')
    ConvertUTF8(f'{EMOTION_RESULT_FOLDER}{file_name}/language.json')

    
@app.route('/speech_idenitfy_download', methods=['get'])
def speech_idenitfy_download():
    
    file_name = request.args.get('name')
    with open('output.txt', 'w') as file:
        # 写入内容到文件
        file.write(f'{file_name}\n')
        
    result_list=os.listdir(SPEECH_RESULT_FOLDER)
    submit_list=os.listdir(SUMIT_FOLDER)
    if(f'{file_name}.json' not in result_list):
        if(f'{file_name}.json' not in submit_list):
            return redirect(url_for('azure'))
        
        f = open(f'./submitFile/{file_name}.json')
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
                # 還沒有翻譯完成
                return redirect(url_for('azure'))
        else:
            # error
            print(result.stderr)
            
    
    return send_file(f'{SPEECH_RESULT_FOLDER}{file_name}.json',as_attachment=True)


@app.route('/emotion_idenitfy_download', methods=['get'])
def emotion_idenitfy_download():
    file_name = request.args.get('name')
    emotion_result_list=os.listdir(EMOTION_RESULT_FOLDER)
    if(f'{file_name}' not in emotion_result_list):
        return redirect(url_for('azure'))
    else:
        if(f'{file_name}.zip' not in emotion_result_list):
            shutil.make_archive(f'{EMOTION_RESULT_FOLDER}{file_name}', 'zip', f'{EMOTION_RESULT_FOLDER}{file_name}')
        
        
    return send_file(f'{EMOTION_RESULT_FOLDER}{file_name}.zip',as_attachment=True)
    
    
    
if __name__ == '__main__':
    app.run()
