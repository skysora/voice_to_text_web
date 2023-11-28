# emotion
from flask import Blueprint, request
import os
import zipfile

from web.module.emotion import *
import web.module.emotion.utils as utils

emotion_blueprint = Blueprint('emotion', __name__, template_folder='templates')


@emotion_blueprint.route('/emotion_idenitfy_download', methods=['GET','POST'])
def emotion_idenitfy_download():
    if request.method == 'GET':
        file_list = [request.args.get('name')]
    
    if request.method == 'POST':
        file_list = request.json['file_list'] 
        
    zip_file_path = f'{EMOTION_RESULT_FOLDER}temp.zip'  
    
    flag=0
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder_name in file_list:
            folder_path = os.path.join(EMOTION_RESULT_FOLDER, folder_name)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                utils.add_folder_to_zip(zipf, folder_path, EMOTION_RESULT_FOLDER)
            else:
                flag += 1
                
    if(flag==len(file_list)):
        return "error"
    else:
        return zip_file_path.replace('/web/data/','')