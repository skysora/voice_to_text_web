# file
from flask import Blueprint, request, redirect, url_for,render_template,send_file, send_from_directory
import os
import json
from azure.storage.blob import BlobServiceClient,BlobServiceClient
import subprocess
import shutil
import threading
from web.database import db 
from web.models.models import File,User
from flask_login import current_user, login_required
from sqlalchemy import not_
import zipfile
from web.module.file import *

file_blueprint = Blueprint('file', __name__, template_folder='templates')


@file_blueprint.route('/delete_file', methods=['get'])
def delete_file():
    file_id = request.args.get('id')
    select_user_id = request.args.get('select_user_id') 
    files = File.query.filter_by(id=file_id, user_id=select_user_id).all()
    other_files = File.query.filter_by(id=file_id).filter(not_(File.user_id == select_user_id)).all()
    
    # 如果没有其他用户与文件关联，则删除文件
    if len(other_files)==0:
        
        #singal
        try:
            if os.path.exists(files[0].singal_file_path):
                os.remove(files[0].singal_file_path)
        except:
            pass
        #speech
        try:
            if os.path.exists(files[0].submit_text_file_path):
                os.remove(files[0].submit_text_file_path)
            if os.path.exists(files[0].origin_text_file_path):
                os.remove(files[0].origin_text_file_path)
        except:
            pass
        #process
        try:
            if os.path.exists(files[0].process_speech_file_path):
                shutil.rmtree(files[0].process_speech_file_path)
        except:
            pass
        #emotion
        try:
            if os.path.exists(files[0].origin_emotion_file_path):
                shutil.rmtree(files[0].origin_emotion_file_path)
            #emotion zip
            if os.path.exists(files[0].origin_emotion_file_path+'.zip'):
                os.remove(files[0].origin_emotion_file_path+'.zip')
        except:
            pass
        #text
        try:
            if os.path.exists(f'{files[0].modified_text_file_path}'):
                os.remove(f'{files[0].modified_text_file_path}')
        except:
            pass
    
    for file in files:   
        db.session.delete(file)
        
    db.session.commit()
        
    return redirect(url_for('view.datatable'))

@file_blueprint.route('/data/<path:filename>')
def data_directory(filename):
     
    return send_from_directory(f'/web/data/',filename)