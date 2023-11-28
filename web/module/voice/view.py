# voice
from flask import Blueprint, request, redirect, url_for,render_template,send_file
import os
import json
import shutil
import threading
from web.database import db 
from web.models.models import File,User
from flask_login import current_user, login_required
from sqlalchemy import not_
import zipfile
from web.module.voice import *
import web.module.voice.utils as utils

voice_blueprint = Blueprint('voice', __name__, template_folder='templates')

@voice_blueprint.route('/upload_voice', methods=['POST'])
@login_required
def upload_voice():
    # Iterate for each file in the files List, and Save them
    files = request.files.getlist('file')
    for file in files:
        # 本地端測試
        filename = file.filename
        # Create a new File object and associate it with the current user
        new_file = File(
            title=filename,
            singal_file_path=os.path.join(UPLOAD_FOLDER, filename),
            user_id=current_user.id  # Assuming your user model has an 'id' field
        )
        db.session.add(new_file)
        db.session.commit()
        file.save(os.path.join(UPLOAD_FOLDER, f"{new_file.id}.wav"))
    return redirect(url_for('view.datatable'))


@voice_blueprint.route('/download_voice', methods=['get'])
def download_voice():
    file_id = request.args.get('id')
    select_user_id = request.args.get('select_user_id') 
    file = File.query.filter_by(id=file_id, user_id=select_user_id).first()
    return send_file(f'{file.singal_file_path}',as_attachment=True)



@voice_blueprint.route('/insert_file_idenitfy', methods=['get'])
def insert_file_idenitfy():
    file_id = request.args.get('id')
    select_user_id = request.args.get('select_user_id') 
    file = File.query.filter_by(id=file_id, user_id=select_user_id).first()
      
    utils.upload_file_to_cloud(file)
    # SPEECH IDENTIFY
    submit_list=os.listdir(SUMIT_FOLDER)
    if(f'{file_id}.json' not in submit_list):
        utils.speech_idenitfy(file_id)
        
    return redirect(url_for('view.datatable'))



@voice_blueprint.route('/speech_idenitfy_download', methods=['GET','POST'])
def voice_idenitfy_download():
    
    if request.method == 'GET':
        file_list = [request.args.get('id')]
    
    if request.method == 'POST':
        file_list = request.json['file_list'] 
        
    
        
    zip_file_path = f'{TEXT_OUTPUT}temp.zip'  
    flag=0
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in file_list:
            output_file_path = f"{TEXT_OUTPUT}{file_name}.txt"
            if os.path.exists(output_file_path):
                zipf.write(output_file_path, os.path.basename(output_file_path))
            else:
                flag += 1
    
        
    if(flag==len(file_list)):
        return "error"
    else:
        return zip_file_path.replace('/web/data/','')
    
    
    
@voice_blueprint.route('/text_file_generate', methods=['get'])
def text_file_generate():
    file_id = request.args.get('id')
    select_user_id = request.args.get('select_user_id') 
    file = File.query.filter_by(id=file_id, user_id=select_user_id).first()
    
    
    text_path = f"{file.process_speech_file_path}/text"
    

    if (not os.path.exists(f"{text_path}")):
        return redirect(url_for('view.datatable'))
    
    output_file_path = f"{TEXT_OUTPUT}{file_id}.txt"
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
        
        
    return redirect(url_for('voice.edit', id=file_id,select_user_id=select_user_id))



@voice_blueprint.route('/edit', methods=['get'])
def edit():
    
    file_id = request.args.get('id')
    select_user_id = request.args.get('select_user_id') 
        
    file = File.query.filter_by(id=file_id, user_id=select_user_id).first()
    user_files = File.query.filter_by(user_id=select_user_id).filter(File.process_speech_file_path.isnot(None)).order_by(File.timestamp.desc()).all()
    

        
    file_list=[]
    for file_temp in user_files:
        if(file_temp.process_speech_file_path != None):  
            file_list.append(str(file_temp.id))
          
    now_index = file_list.index(file_id)
    
    
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
    file_info = {"file_name":file.title,"id":file.id,'previous_file':previous_file_title,'next_file':next_file_title,'audio':audio_path}
    

    audio_path = f'{file.process_speech_file_path}/audio/'
    text_path = f'{file.process_speech_file_path}/text/'
    remark_path = f'{file.process_speech_file_path}/remark/'
    
    if(not os.path.exists(remark_path)):
        os.mkdir(f'{remark_path}')  
    file_list=[]
    data={}
    for i in range(len(os.listdir(audio_path))):
        remark_data = ""
        text_data = ""
        file_list.append(f'{i}')
        try:
            with open(f'{text_path}{i}.txt') as file_text:
                text_data = ''.join(file_text.readlines())
        except:
            pass
           
        try:     
            if(os.path.exists(f'{remark_path}{i}.txt')):
                with open(f'{remark_path}{i}.txt') as file_text:
                    remark_data = ''.join(file_text.readlines())
        except:     
            pass
        
        audio = f"{audio_path}{i}.mp3".replace(f'/web/data/','')
        data[f'{i}'] = {"text":text_data,"audio":f"{audio}","remark":remark_data}

    return render_template('view/info.html',data=data,file_list=file_list,message="success",file_info=file_info,select_user_id=select_user_id)
          
@voice_blueprint.route('/edit_file', methods=['POST'])
def edit_file():
    data = request.json  # 解析JSON数据
    file_id = data.get('file_id')
    editedText = data.get('editedText')
    editedRemark = data.get('editedRemark')
    pharses = data.get('pharses')
    select_user_id = data.get('select_user_id') 
    
    
    file = File.query.filter_by(id=file_id, user_id=select_user_id).first()

            
    text_path = f'{file.process_speech_file_path}/text/{pharses}.txt'
    remark_path = f'{file.process_speech_file_path}/remark/{pharses}.txt'
    
    
    if(os.path.exists(text_path)):
        os.remove(text_path)
        
    if(os.path.exists(remark_path)):
        os.remove(remark_path)
        
        
    with open(text_path, 'w', encoding='utf-8') as file:
        file.write(editedText.replace('\n',''))
      
    with open(remark_path, 'w', encoding='utf-8') as file:
        file.write(editedRemark.replace('\n',''))
    
    if(editedRemark.replace(' ','').replace('\n','') ==''):
        os.remove(remark_path)
          
    return redirect(url_for('voice.edit', id=file_id,select_user_id=select_user_id))

