source myenv/bin/activate

flask db init -d web/migrations/
flask db migrate -d web/migrations/ -m "Update model with new column"
flask db  upgrade -d web/migrations/



/home/ec2-user/myweb
sudo vim /etc/systemd/system/myweb.service
sudo systemctl daemon-reload
sudo systemctl start myweb
sudo systemctl enable myweb
sudo systemctl status myweb
curl localhost:8000

gunicorn -b 0.0.0.0:5000 app:app 
sudo vim /etc/nginx/nginx.conf

openssl genrsa -out private_key.pem 2048
openssl rsa -pubout -in private_key.pem -out public_key.pem

docker run -it --rm msftspeech/spx

sudo docker run -it -v ./web-server:/data --rm msftspeech/spx spx config @key --set a255b150359e4b37be57dce02c44d1c0
sudo docker run -it -v ./web-server:/data --rm msftspeech/spx spx config @region --set eastus
sudo docker run -it -v ./web-server:/data --rm msftspeech/spx spx recognize --file ./data/English.wav

#英文
sudo docker run -it -v ./web-server:/data --rm msftspeech/spx spx batch transcription create --name "My Transcription" --language "en-US" --content https://ntuststorage1.blob.core.windows.net/test/English.wav

#中文
/root/.dotnet/tools/spx batch transcription create --language "zh-CN" --name "北鼻故事屋Baby Story【三隻小豬】｜ 愛比姊姊說故事.mp3" --content "https://ntuststorage2.blob.core.windows.net/ntustvoice/北鼻故事屋Baby Story【三隻小豬】｜ 愛比姊姊說故事.mp3"
spx batch transcription create --language "zh-CN" --name "My Transcription" --content https://ntuststorage2.blob.core.windows.net/ntustvoice/IC0001W0086.wav >> ./result/test.json



spx batch transcription status --api-version v3.1 --transcription 0fd34a89-9402-4a2c-a4ff-e876f6f310a8
spx batch transcription list --api-version v3.1 --files --transcription 073a526d-29f9-4477-860e-e62c9f20a954


wget -O ./speechResult/IC0001W0086.wav.json "https://spsvcprodeus.blob.core.windows.net/bestor-c6e3ae79-1b48-41bf-92ff-940bea3e5c2d/TranscriptionData/2738e751-1760-4f29-93ff-582a5f8f44a6_0_0.json?skoid=50c6251a-ac54-47a3-9265-a1e4f84be9b9&sktid=33e01921-4d64-4f8c-a055-5bdaffd5e33d&skt=2023-10-11T10%3A05%3A51Z&ske=2023-10-16T10%3A10%3A51Z&sks=b&skv=2023-08-03&sv=2023-08-03&st=2023-10-11T10%3A05%3A51Z&se=2023-10-11T22%3A10%3A51Z&sr=b&sp=rl&sig=sGXlz0a4u%2FqgdfxZHjO41ftJeb5%2FUdRijAKV1xE%2FiN8%3D"
