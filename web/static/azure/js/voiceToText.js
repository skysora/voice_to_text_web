// status fields and start button in UI
var VoiceToText_microphone_phraseDiv;
var VoiceToText_microphone_startRecognizeOnceAsyncButton;
var VoiceToText_file_phraseDiv;
var VoiceToText_file_startRecognizeOnceAsyncButton;

// subscription key and region for speech services.
var SpeechSDK;
var recognizer;
var speechConfig


document.addEventListener("DOMContentLoaded", function() {


    //microphone
    VoiceToText_microphone_startRecognizeOnceAsyncButton = document.getElementById("VoiceToText_microphone_startRecognizeOnceAsyncButton");
    VoiceToText_microphone_phraseDiv = document.getElementById("VoiceToText_microphone_phraseDiv");

    VoiceToText_microphone_startRecognizeOnceAsyncButton.addEventListener("click", function() {

        speechConfig = SpeechSDK.SpeechConfig.fromSubscription(subscription, ServiceRegion);
        VoiceToText_microphone_startRecognizeOnceAsyncButton.disabled = true;
        VoiceToText_microphone_phraseDiv.innerHTML = "";

        speechConfig.speechRecognitionLanguage = document.getElementById("VoiceToText_microphone_language").value;


        var audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
        recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

        recognizer.recognizeOnceAsync(
            function(result) {
                VoiceToText_microphone_startRecognizeOnceAsyncButton.disabled = false;
                VoiceToText_microphone_phraseDiv.innerHTML += result.text;
                window.console.log(result);

                recognizer.close();
                recognizer = undefined;
            },
            function(err) {
                VoiceToText_microphone_startRecognizeOnceAsyncButton.disabled = false;
                VoiceToText_microphone_phraseDiv.innerHTML += err;
                window.console.log(err);

                recognizer.close();
                recognizer = undefined;
            });
    });

    //file
    VoiceToText_file_startRecognizeOnceAsyncButton = document.getElementById("VoiceToText_file_startRecognizeOnceAsyncButton");
    VoiceToText_file_phraseDiv = document.getElementById("VoiceToText_file_phraseDiv");
    filePicker = document.getElementById("VoiceToText_file_filePicker");


    filePicker.addEventListener("change", function () {
        audioFile = filePicker.files[0];
        VoiceToText_file_startRecognizeOnceAsyncButton.disabled = false;
    });

    VoiceToText_file_startRecognizeOnceAsyncButton.addEventListener("click", function () {

        speechConfig = SpeechSDK.SpeechConfig.fromSubscription(subscription, ServiceRegion);
        VoiceToText_file_startRecognizeOnceAsyncButton.disabled = true;
        VoiceToText_file_phraseDiv.innerHTML = "";

        speechConfig.speechRecognitionLanguage = document.getElementById("VoiceToText_file_language").value;
        console.log(speechConfig.speechRecognitionLanguage)

        //將上傳檔案
        var audioConfig  = SpeechSDK.AudioConfig.fromWavFileInput(audioFile);
        recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

        recognizer.recognizeOnceAsync(
            function (result) {
            VoiceToText_file_startRecognizeOnceAsyncButton.disabled = false;
            VoiceToText_file_phraseDiv.innerHTML += result.text;
            window.console.log(result);

            recognizer.close();
            recognizer = undefined;
            },
            function (err) {
                VoiceToText_file_startRecognizeOnceAsyncButton.disabled = false;
                VoiceToText_file_phraseDiv.innerHTML += err;
            window.console.log(err);

            recognizer.close();
            recognizer = undefined;
        });
    });

    let audioChunks = [];
    // 保存音频数据为文件
    function saveAudioToFile() {
        if (audioChunks.length > 0) {
            console.log("save")
            var audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            var downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(audioBlob);
            downloadLink.download = 'recorded-audio.wav';
            downloadLink.click();
        }
    }
    var  mediaRecorder;
    function gotLocalMediaStream(mediaStream) {
        mediaRecorder = new MediaRecorder(mediaStream);

        console.log(mediaRecorder)
        mediaRecorder.ondataavailable = (event) => {
            console.log("push")
            /* add the data to the recordedDataArray */
            audioChunks.push(event.data)
        }
        mediaRecorder.ondataavailable = function(event) {
            // event.data 包含录制的音频数据
        
            if (event.data.size > 0) {
                console.log("123321")
                // 处理音频数据，例如发送到服务器、保存到本地文件等
                // event.data 是一个 Blob 对象，您可以将其转换为其他格式或直接使用
            }
        };
        setTimeout(function() {
            console.log("3s")
            mediaRecorder.stop();
        }, 10000);
    }

    document.querySelector('#get-access').addEventListener('click', async function init(e) {


        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        }).then(gotLocalMediaStream)
        // const mediaRecorder = new MediaRecorder(stream);
        // mediaRecorder.ondataavailable = (event) => {
        //     console.log("push")
        //     /* add the data to the recordedDataArray */
        //     audioChunks.push(event.data)
        // }
        // mediaRecorder.onstop = function() {
        //     saveAudioToFile();
        // };

        // var audioConfig  = SpeechSDK.AudioConfig.fromStreamInput(stream);
    })


    if (!!window.SpeechSDK) {
        SpeechSDK = window.SpeechSDK;
        VoiceToText_microphone_startRecognizeOnceAsyncButton.disabled = false;
        VoiceToText_file_startRecognizeOnceAsyncButton.disabled = false;

        document.getElementById('VoiceToText_microphone').style.display = 'block';
        document.getElementById('VoiceToText_file').style.display = 'block';
    }
});