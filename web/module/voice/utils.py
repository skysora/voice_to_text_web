


from azure.storage.blob import BlobServiceClient,BlobServiceClient
import subprocess
import json
from web.module.voice import *



def upload_file_to_cloud(file):
    
    with open(f'{TOKEN_PATH}', 'r') as token_file:
        data = json.load(token_file)
        
    command  = f'/root/.dotnet/tools/spx config @key --set {data["voiceKey"]}'
    subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    command  = f'/root/.dotnet/tools/spx config @region --set {data["voiceLocation"]}'
    subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # upload file to cloud
    blob_service_client = BlobServiceClient.from_connection_string(data['blob_service_client_string'])
        
        
    upload_file_path = file.singal_file_path
    
    with open('./web/test.txt','w') as test:
        test.write(str(upload_file_path))
    blob_client = blob_service_client.get_blob_client(container='ntustvoice', blob=f"{file.id}.wav")
    # Upload the created file
    try:
        with open(file=upload_file_path, mode="rb") as data:
            blob_client.upload_blob(data)
    except:
        pass
    
def speech_idenitfy(file_id):
    
    with open(f'{TOKEN_PATH}', 'r') as test:
        data = json.load(test)
        
    blob_name = data['blob_name']
    command  = f'/root/.dotnet/tools/spx batch transcription create --language "zh-CN" --name "{file_id}" --content "https://{blob_name}.blob.core.windows.net/ntustvoice/{file_id}.wav"'
    
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
        
