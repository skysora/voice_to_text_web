# view.py
from flask import Blueprint, render_template,request,jsonify
from flask_login import current_user
from web.models.models import File
from web.database import db
import threading
from web.models.models import User,UserRoleEnum

import web.module.view.utils as utils
from web.module.view import *
import json
import csv
import os
import re
view_blueprint = Blueprint('view', __name__, template_folder='templates/view')

@view_blueprint.route("/datatable", methods=['GET','POST'])
def datatable():
    
    
    all_users=None
    user = User.query.filter_by(id=current_user.id).first()
    #判斷權限
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
    
    # 決定顯示檔案開始和結束位置
    start=0
    if request.method == 'POST':
        select_user_id = request.json['select_user_id']     
        page_limit = int(request.json['page_limit'])
        page_number = int(request.json['page_number'])
        count = File.query.filter_by(user_id=select_user_id).count()
        if page_number>1:
            start = (page_number-1)*page_limit
            end = min(count,page_number*page_limit)
        else:
            end = min(count,page_limit)
    else:
        select_user_id = current_user.id
        count = File.query.filter_by(user_id=select_user_id).count()
        page_limit = count
        page_number = 1
        end = min(count,page_limit)
        
    select_user_flag = int(select_user_id)==int(current_user.id)
    

    file_list = File.query.filter_by(user_id=select_user_id).order_by(File.timestamp.desc()).slice(start, end).with_entities(File.id).all()
    file_list = [str(file[0]) for file in file_list]


    total_files  = File.query.filter_by(user_id=select_user_id).order_by(File.timestamp.desc()).all()
    
    
    data={}
    for file in total_files: 
        file_name = f'{file.title}'
        file_id = f'{file.id}'
        # speech 代表 是否辨識完成
        # submit 代表 是否上傳辨識
        # emotion 代表 情緒辨識是否完成
        # edit 代表 辨識完的結果是否切割完成
        # text 代表 是否檢查過
        
        data[file_id] = {'filename':file_name,
                        'result':{'submit':False,"speech":False,"process_speech":False,'text':False,'emotion':False,'remark':False},'datetime':'',
                        'User':f'{User.query.filter_by(id=file.user_id).first().username}'}
        data[file_id]['datetime'] = f'{file.timestamp}'
        
        
        # 檢查這個檔案的答案是不是已經在資料夾內
        file = utils.check_exitst_path(file)
        
        # 檢查這個檔案的答案
        data = utils.check_exist_answer(file,data)

          
        if( (not data[file_id]['result']['submit']) and (not data[file_id]['result']['speech']) and (not data[file_id]['result']['process_speech']) and (not data[file_id]['result']['text']) and (not data[file_id]['result']['emotion'])):
            
            data[file_id]['status'] = "NotYet" 
            
        elif(data[file_id]['result']['process_speech'] and data[file_id]['result']['text'] and data[file_id]['result']['emotion']):
            
            data[file_id]['status'] = "Finish" 
            
        #如果上傳了還沒有結果，檢查完成了沒
        elif(data[file_id]['result']['submit'] and (not data[file_id]['result']['speech'])):
            data[file_id]['status'] = "Speech Identify Waiting"
            task_thread = threading.Thread(target=utils.check_submit_speech,
                                        args=((file_id,)))
            task_thread.start()
        #如果有結果，但還沒做前處理，做前處理
        elif (data[file_id]['result']['speech'] and (not data[file_id]['result']['process_speech'])):
            data[file_id]['status'] = "Split file Waiting"
            file.process_speech_file_path = f'{PROCESS_SPEECH_RESULT_FOLDER}{file_id}'
            db.session.commit()
            with open(file.origin_text_file_path,'r') as file_text:
                text_data = json.load(file_text)
            try:
                text_data['recognizedPhrases']
            except:
                # os.remove(file.origin_text_file_path)
                data[file_id]['status'] = "Error" 
                continue
            task_thread = threading.Thread(target=utils.generate_process_speech_result,
                                        args=((file.origin_text_file_path, #singal identity result path
                                               file.singal_file_path,      #origin singal path
                                               file.process_speech_file_path #singal identity process path
                                                )))
            task_thread.start()
            
        elif(data[file_id]['result']['process_speech'] and (not data[file_id]['result']['text'])):
            data[file_id]['status'] = "Text Waiting"
            
        # 如果做過做前處理，可以產生情緒辨識檔案emotion_text_file
        elif (data[file_id]['result']['speech'] and data[file_id]['result']['text'] ):
            data[file_id]['status'] = "Emototion Waiting" 
            # task_thread = threading.Thread(target=utils.emotion_identify,args=((file_idfile.process_speech_file_path)))
            # task_thread.start()
        else:
            data[file_id]['status'] = "Waiting" 
        
        
    return render_template('view/datatable.html',data=data,file_list = file_list,file_list_number=count,
                           currentPage=page_number,user_list = all_users,page_limit=page_limit,
                           select_user_id = select_user_id,select_user_flag = select_user_flag,
                           )
    

@view_blueprint.route("/manage")
def manage():
    user = User.query.filter_by(id=current_user.id).first()
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
        total_data = []
        for user in all_users:
            data = {"username":"","upload":"","speech":"","emotion":"","text":"","total":""}
            data["username"]  = user.username
            data["upload"]  = File.query.filter(File.user_id == user.id, File.singal_file_path.isnot(None)).count()
            data["speech"]  = File.query.filter(File.user_id == user.id, File.origin_text_file_path.isnot(None)).count()
            data["emotion"]  = File.query.filter(File.user_id == user.id, File.origin_emotion_file_path.isnot(None)).count()
            data["text"]  = File.query.filter(File.user_id == user.id, File.modified_text_file_path.isnot(None)).count()
            data["total"]  = File.query.filter(File.user_id == user.id, 
                                               File.origin_text_file_path.isnot(None),
                                               File.origin_emotion_file_path.isnot(None),
                                               File.modified_text_file_path.isnot(None),
                                               ).count()
            data["time"] = 0
            try:
                data["total"] = int(data["total"]/data["upload"]*100)
            except:
                data["total"] = 0
            total_data.append(data)
            
            
            finish_file = File.query.filter(File.user_id == user.id, 
                                                File.origin_text_file_path.isnot(None),
                                                File.origin_emotion_file_path.isnot(None),
                                                File.modified_text_file_path.isnot(None),
                                                )

        return render_template('view/manage.html',user_list=total_data)
    else:
        return render_template('view/manage.html',user_list=None)
    
    
@view_blueprint.route("/export")
def export():
    
    all_users=None
    user = User.query.filter_by(id=current_user.id).first()
    #判斷權限
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
        
    return render_template('view/export.html',user_list = all_users)


@view_blueprint.route('/data/table_json')
def table_json():
    
    # Define the columns you want to include
    desired_columns = ['頻道名稱', '影片發佈時間', '影片連結', '影片長度', 'WAV檔名']
    singal = [file.title for file in File.query.all()]
    edit  = os.listdir(f'{TEXT_OUTPUT}')
    edit = [re.sub(r".txt", "", item) for item in edit]
    emotion  = os.listdir(f'{EMOTION_RESULT_FOLDER}')
    
    # Query titles based on the IDs
    edit_titles = []
    emotion_titles = []
    
    # Loop through each ID in 'edit'
    for id in edit:
        # Try to find a File record with the matching ID
        file = File.query.filter_by(id=id).first()
        # If a matching record is found, append its title to the 'titles' list
        if file:
            edit_titles.append(file.title)
    
    # Loop through each ID in 'emotion'
    for id in emotion:
        # Try to find a File record with the matching ID
        file = File.query.filter_by(id=id).first()
        # If a matching record is found, append its title to the 'titles' list
        if file:
            emotion_titles.append(file.title)
            
    singal = [re.sub(r".wav", "", item) for item in singal]
    edit_titles = [re.sub(r".wav", "", item) for item in edit_titles]
    emotion_titles = [re.sub(r".wav", "", item) for item in emotion_titles]     
            
        
    # Note the use of 'utf-8-sig' encoding instead of 'utf-8'
    with open('web/module/view/table.csv', mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        data=[]
        for row in reader:
            row = {k: row[k] for k in desired_columns if k in row}
            file = File.query.filter_by(title=f'{row["WAV檔名"]}.wav').first()
            
            if(file):
                row['id'] = file.id
            else:
                row['id'] = "None"
                
            # singal
            if(row['WAV檔名'] in singal):
                row['match'] = "ok-match"
            else:
                row['match'] = "non-match"
            # edit
            if(row['WAV檔名'] in edit_titles):
                row['edit'] = "ok-edit"
            else:
                row['edit'] = "non-edit"
            # emotion   
            if(row['WAV檔名'] in emotion_titles):
                row['emotion'] = "ok-finish"
            else:
                row['emotion'] = "non-finish"
            data.append(row)
                
    return jsonify(data)
