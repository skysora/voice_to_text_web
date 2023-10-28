# view.py
from flask import Blueprint, render_template,request
import os
import json
from flask_login import current_user
from web.models.models import File
from web.database import db
import threading
from web.models.models import User,UserRoleEnum
import web.view.utils as utils

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
    
    #判斷權限
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
    
    if request.method == 'POST':
        select_user_id = request.json['select_user_id']     
    else:
        select_user_id = current_user.id
        
    select_user_flag = int(select_user_id)==int(current_user.id)
    user_files = File.query.filter_by(user_id=select_user_id).order_by(File.timestamp.desc()).all()
    file_list=[file.title for file in user_files]
    
    # 決定顯示檔案開始和結束位置
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
        # speech 代表 是否辨識完成
        # submit 代表 是否上傳辨識
        # emotion 代表 情緒辨識是否完成
        # edit 代表 辨識完的結果是否切割完成
        # text 代表 是否檢查過
        
        data[file_name] = {'result':{'submit':False,"speech":False,"process_speech":False,'text':False,'emotion':False},'datetime':'',
                           'User':f'{User.query.filter_by(id=file.user_id).first().username}'}
        data[file_name]['datetime'] = f'{file.timestamp}'
        
        
        # 檢查這個檔案的答案是不是已經在資料夾內
        file = utils.check_exitst_path(file)
        
        
        
        # 檢查這個檔案的答案
        data = utils.check_exitst_answer(file,data)

        #如果上傳了還沒有結果，檢查完成了沒
        if (data[file_name]['result']['submit'] and not data[file_name]['result']['speech']):
            utils.check_submit_speech(file_name)
        
        #如果有結果，但還有做前處理，做前處理
        if (data[file_name]['result']['speech'] and (not data[file_name]['result']['process_speech'])):
            file.process_speech_file_path = f'{PROCESS_SPEECH_RESULT_FOLDER}{file_name}'
            db.session.commit()
            task_thread = threading.Thread(target=utils.generate_process_speech_result,
                                        args=((file.origin_text_file_path, #singal identity result path
                                               file.singal_file_path,      #origin singal path
                                               file.process_speech_file_path #singal identity process path
                                                )))
            task_thread.start()
        
        
        # 如果做過做前處理，可以產生情緒辨識檔案
        if (data[file_name]['result']['text']):
            task_thread = threading.Thread(target=utils.emotion_identify,args=((file.title,file.process_speech_file_path)))
            task_thread.start()

        
        # 檢查這個檔案的答案
        data = utils.check_exitst_answer(file,data)
        
            
        #判斷狀態
        if(data[file_name]['result']['speech'] and data[file_name]['result']['text'] and data[file_name]['result']['emotion']):
            data[file_name]['status'] = "Finish"  
            
        elif(not data[file_name]['result']["submit"] and not data[file_name]['result']['speech'] and not data[file_name]['result']['text'] and not data[file_name]['result']['emotion']):
            data[file_name]['status'] = "NotYet" 
              
        elif(data[file_name]['result']["submit"] and (not data[file_name]['result']['speech'])):
            data[file_name]['status'] = "Process Speech Waiting"    
            
        elif(not data[file_name]['result']['text'] and data[file_name]['result']['process_speech']):
            data[file_name]['status'] = "Text Waiting"
            
        elif(data[file_name]['result']['speech'] and data[file_name]['result']['text'] and not data[file_name]['result']['emotion']):
            data[file_name]['status'] = "Emototion Waiting" 
        else:
            data[file_name]['status'] = "Waiting" 
    
            
    return render_template('view/azure.html',data=data,file_list = file_list[(page_number-1)*page_limit:page_number*page_limit],
                           file_list_number=len(user_files),currentPage=page_number,user_list = all_users,
                           select_user_id = select_user_id,select_user_flag = select_user_flag,
                           )
    
    
@view_blueprint.route("/manage")
def manage():
    user = User.query.filter_by(id=current_user.id).first()
    if (user.permissions == UserRoleEnum.ADMIN):
        all_users =  User.query.all()
        total_data = []
        temp={}
        for user in all_users:
            data = {"username":"","upload":"","speech":"","emotion":"","text":"","total":""}
            data["username"]  = user.username
            data["upload"]  = len(File.query.filter_by(user_id=user.id).all())
            data["speech"]  = 0
            data["emotion"]  = 0
            data["text"]  = 0
            data["total"]  = 0
            for file in File.query.filter_by(user_id=user.id).all():
                file_name = file.title
                temp[file_name] = {'result':{'submit':False,"speech":False,"process_speech":False,'text':False,'emotion':False}}
                temp = utils.check_exitst_answer(file,temp)
                # speech
                if(os.path.exists(file.singal_file_path)):
                    data["speech"]+=1
                # emotion
                data["emotion"]+=temp[file_name]['result']["emotion"] 
                # text
                data["text"]+=temp[file_name]['result']["text"]  
                # total
                if(temp[file_name]['result']["speech"] and temp[file_name]['result']["emotion"] and temp[file_name]['result']["text"]):
                    data["total"]  += 1
            try:
                data["total"] = int(data["total"]/data["upload"]*100)
            except:
                data["total"] = 0
            total_data.append(data)
        return render_template('view/manage.html',user_list=total_data)
    else:
        return render_template('view/manage.html',user_list=None)


    

    