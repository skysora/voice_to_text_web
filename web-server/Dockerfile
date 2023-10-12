
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y wget apt-transport-https
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt-get update
RUN apt-get install -y dotnet-sdk-6.0
RUN dotnet tool install --global Microsoft.CognitiveServices.Speech.CLI

RUN apt install libgstreamer1.0-0 -y \
gstreamer1.0-plugins-base -y \
gstreamer1.0-plugins-good -y \
gstreamer1.0-plugins-bad -y \
gstreamer1.0-plugins-ugly -y


ENV PATH="${PATH}:/root/.dotnet/tools"

RUN spx config @key --set a255b150359e4b37be57dce02c44d1c0
RUN spx config @region --set eastus

RUN apt install python3.8-distutils -y

RUN apt install python3.8 -y
RUN apt install curl -y
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN python3.8 get-pip.py
COPY ./requirements.txt /requirements.txt 
RUN pip3 install -r /requirements.txt
RUN apt install vim -y


WORKDIR /web-server 
CMD gunicorn app:app -c gunicorn.conf.py