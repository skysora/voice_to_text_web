# identifly.py
from flask import Blueprint,Flask, request, redirect, url_for,render_template,send_file, send_from_directory
import os
import json
from azure.storage.blob import BlobServiceClient,BlobServiceClient,generate_container_sas,BlobSasPermissions
import subprocess
import shutil
import threading
from web.database import db 
from web.models.models import File,User
from flask_login import current_user, login_required
from opencc import OpenCC
from sqlalchemy import not_

identity_blueprint = Blueprint('identify', __name__, template_folder='templates')
UPLOAD_FOLDER = '/web/data/signal/'
SPEECH_RESULT_FOLDER = '/web/data/speechResult/'
SUMIT_FOLDER = '/web/data/submitFile/'
EMOTION_RESULT_FOLDER = '/web/data/emotionResult/'
PROCESS_SPEECH_RESULT_FOLDER = '/web/data/process_speechResult/'
TEXT_OUTPUT = '/web/data/output/'
TOKEN_PATH="/web/token.json"

@identity_blueprint.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    # Iterate for each file in the files List, and Save them
    files = request.files.getlist('files[]')
    for file in files:
        # 本地端測試
        filename = file.filename
        db_files = File.query.filter_by(title=filename,user_id=current_user.id).all()
        if len(db_files)>0:
            filename  = f'{filename}'.replace('.',f'_{len(db_files)+1}.')
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # Create a new File object and associate it with the current user
        new_file = File(
            title=filename,
            singal_file_path=os.path.join(UPLOAD_FOLDER, filename),
            user_id=current_user.id  # Assuming your user model has an 'id' field
        )
        db.session.add(new_file)
    db.session.commit()
    return redirect(url_for('view.azure'))
      
@identity_blueprint.route('/download_file', methods=['get'])
def download_file():
    file_name = request.args.get('name')
    file = File.query.filter_by(title=file_name, user_id=current_user.id).first()
    return send_file(f'{file.singal_file_path}',as_attachment=True)


@identity_blueprint.route('/delete_file', methods=['get'])
def delete_file():
    file_name = request.args.get('name')
    files = File.query.filter_by(title=file_name, user_id=current_user.id).all()
    other_files = File.query.filter_by(title=file_name).filter(not_(File.user_id == current_user.id)).all()
    
    # 如果没有其他用户与文件关联，则删除文件
    if len(other_files)==0:
        #singal
        try:
            if os.path.exists(file.singal_file_path):
                os.remove(file.singal_file_path)
        except:
            pass
        #speech
        try:
            if os.path.exists(file.submit_text_file_path):
                os.remove(file.submit_text_file_path)
            if os.path.exists(file.origin_text_file_path):
                os.remove(file.origin_text_file_path)
        except:
            pass
        #process
        try:
            if os.path.exists(file.process_speech_file_path):
                shutil.rmtree(file.process_speech_file_path)
        except:
            pass
        #emotion
        try:
            if os.path.exists(file.origin_emotion_file_path):
                shutil.rmtree(file.origin_emotion_file_path)
            #emotion zip
            if os.path.exists(file.origin_emotion_file_path+'.zip'):
                os.remove(file.origin_emotion_file_path+'.zip')
        except:
            pass
        #text
        try:
            if os.path.exists(f'{file.modified_text_file_path}'):
                os.remove(f'{file.modified_text_file_path}.txt')
        except:
            pass
    
    for file in files:   
        db.session.delete(file)
        db.session.commit()
    return redirect(url_for('view.azure'))


@identity_blueprint.route('/insert_file_idenitfy', methods=['get'])
def insert_file_idenitfy():
    file_name = request.args.get('name')
    file = File.query.filter_by(title=file_name, user_id=current_user.id).first()
    
    with open(f'{TOKEN_PATH}', 'r') as file:
        data = json.load(file)
        
    command  = f'/root/.dotnet/tools/spx config @key --set {data["voiceKey"]}'
    subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    command  = f'/root/.dotnet/tools/spx config @region --set {data["voiceLocation"]}'
    subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # upload file to cloud
    blob_service_client = BlobServiceClient.from_connection_string(data['blob_service_client_string'])
    upload_file_path = file.singal_file_path
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
        
    return redirect(url_for('view.azure'))

        
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
        

@identity_blueprint.route('/speech_idenitfy_download', methods=['get'])
def speech_idenitfy_download():
    
    file_name = request.args.get('name')
        
    file = File.query.filter_by(title=file_name, user_id=current_user.id).first()
    
    
    text_path = f"{file.process_speech_file_path}/text"
    
    if (not os.path.exists(f"{text_path}")):
        return redirect(url_for('azure'))
    
    output_file_path = f"{TEXT_OUTPUT}{file_name}.txt"
    # 打开输出文件以进行写入
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        # 遍历指定目录下的所有文件
        for filename in range(len(os.listdir(f"{text_path}"))):
            
            file_path = os.path.join(f"{text_path}", f'{filename}.txt')

            # 打开并读取当前文本文件的内容
            with open(file_path, "r", encoding="utf-8") as input_file:
                file_contents = input_file.read()

                # 将当前文本文件的内容写入输出文件
                output_file.write(file_contents)
                output_file.write("\n")  # 在每个文件的内容之间添加换行符
    

    return send_file(f'{output_file_path}',as_attachment=True)


@identity_blueprint.route('/emotion_idenitfy_download', methods=['get'])
def emotion_idenitfy_download():
    file_name = request.args.get('name')
    file = File.query.filter_by(title=file_name, user_id=current_user.id).first()
    emotion_result_list=os.listdir(EMOTION_RESULT_FOLDER)
    if(f'{file_name}' not in emotion_result_list):
        return redirect(url_for('azure'))
    else:
        if(f'{file_name}.zip' not in emotion_result_list):
            shutil.make_archive(f'{EMOTION_RESULT_FOLDER}{file_name}', 'zip', f'{EMOTION_RESULT_FOLDER}{file_name}')
        
        
    return send_file(f'{EMOTION_RESULT_FOLDER}{file_name}.zip',as_attachment=True)
    
@identity_blueprint.route('/text_file_generate', methods=['get'])
def text_file_generate():
    file_name = request.args.get('name')
    select_user_id = request.args.get('select_user_id') 
    file = File.query.filter_by(title=file_name, user_id=select_user_id).first()
    
    
    text_path = f"{file.process_speech_file_path}/text"
    

    if (not os.path.exists(f"{text_path}")):
        return redirect(url_for('view.azure'))
    
    output_file_path = f"{TEXT_OUTPUT}{file_name}.txt"
    # 打开输出文件以进行写入
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        # 遍历指定目录下的所有文件
        for filename in range(len(os.listdir(f"{text_path}"))):
            
            file_path = os.path.join(f"{text_path}", f'{filename}.txt')

            # 打开并读取当前文本文件的内容
            with open(file_path, "r", encoding="utf-8") as input_file:
                file_contents = input_file.read()

                # 将当前文本文件的内容写入输出文件
                output_file.write(file_contents)
                output_file.write("\n")  # 在每个文件的内容之间添加换行符
        
        
    return redirect(url_for('identify.edit', name=file_name,select_user_id=select_user_id))


@identity_blueprint.route('/edit', methods=['get'])
def edit():
    
    file_name = request.args.get('name')
    select_user_id = request.args.get('select_user_id') 
        
    file = File.query.filter_by(title=file_name, user_id=select_user_id).first()
    user_files = File.query.filter_by(user_id=select_user_id).filter(File.process_speech_file_path.isnot(None)).order_by(File.timestamp.desc()).all()
    
    file_list=[]
    for file_temp in user_files:
        if(file_temp.process_speech_file_path != None):
            file_list.append(file_temp.title)
        
    now_index = file_list.index(file_name)
    
    
    # 前一頁
    if(now_index-1<0):
        previous_file_title = file_list[len(file_list)-1]
    else:
        previous_file_title = file_list[now_index-1]
        
    # 後一頁
    if(now_index+1==len(file_list) or (now_index==0 and len(file_list)==1)):
        next_file_title = file_list[0]
    else:
        next_file_title = file_list[now_index+1]
    
        
    audio_path = file.singal_file_path.replace('/web/data','')
    file_info = {"file_name":file_name,'previous_file':previous_file_title,'next_file':next_file_title,'audio':audio_path}
    

    converter = OpenCC('s2twp')
    audio_path = f'{file.process_speech_file_path}/audio/'
    text_path = f'{file.process_speech_file_path}/text/'
            
    file_list=[]
    data={}
    for i in range(len(os.listdir(audio_path))):
        file_list.append(f'{i}')
        with open(f'{text_path}{i}.txt') as file_text:
            try:
                text_data = file_text.readlines()[0]
            except:
                text_data = ""
        
        
        audio = f"{audio_path}{i}.mp3".replace(f'/web/data/','')
        data[f'{i}'] = {"text":converter.convert(text_data),"audio":f"{audio}"}
        

    return render_template('view/info.html',data=data,file_list=file_list,message="success",file_info=file_info,select_user_id=select_user_id)
          
@identity_blueprint.route('/edit_file', methods=['POST'])
def edit_file():
    data = request.json  # 解析JSON数据
    file_name = data.get('file_name')
    editedText = data.get('editedText')
    pharses = data.get('pharses')
    select_user_id = data.get('select_user_id') 
    
    
    file = File.query.filter_by(title=file_name, user_id=select_user_id).first()

    text_path = f'{file.process_speech_file_path}/text/{pharses}.txt'
    
    with open(text_path, 'w', encoding='utf-8') as file:
        file.write(editedText)
    
          
    return redirect(url_for('identify.edit', name=file_name,select_user_id=select_user_id))


@identity_blueprint.route('/data/<path:filename>')
def data_directory(filename):
     
    return send_from_directory(f'/web/data/',filename)
    
