
FROM ubuntu:20.04

# 安裝基本軟件包和dotnet SDK
RUN apt-get update && apt-get install -y wget apt-transport-https && \
    wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y dotnet-sdk-6.0

# 安裝Python 3.8和一些額外軟件包
RUN apt-get install -y python3.8 python3.8-distutils ffmpeg wget

# 安裝pip
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.8 get-pip.py

# 安裝Python依賴項
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# 安裝其他Python庫
COPY ./packages/flask-login /packages/flask-login
RUN pip install /packages/flask-login
RUN pip install matplotlib --no-cache-dir --force-reinstall
# 安裝Microsoft.CognitiveServices.Speech.CLI工具
RUN dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI

# 設置環境變數
ENV PATH="${PATH}:/root/.dotnet/tools"

# 定義容器啟動命令
CMD gunicorn app:app -c ./web/gunicorn.conf.py --pythonpath ./web

