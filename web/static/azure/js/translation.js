// status fields and start button in UI
var resultsDivs;
var microphone_startRecognizeOnceAsyncButton;

// subscription key and region for speech services.
var languageTargetOptions;
var SpeechSDK;
var recognizer;
var speechConfig
document.addEventListener("DOMContentLoaded", function() {

    

    //micorphone
    microphone_startRecognizeOnceAsyncButton = document.getElementById("microphone_startRecognizeOnceAsyncButton");

    micorphone_languageSourceOptions = document.getElementById("micorphone_languageSourceOptions");

    micorphone_languageTargetOptions = [
        document.getElementById("micorphone_languageTargetOptions1"),
        document.getElementById("micorphone_languageTargetOptions2")
    ];
    micorphone_resultsDivs = [
        document.getElementById("micorphone_phraseDiv1"),
        document.getElementById("micorphone_phraseDiv2")
    ];

    //micorphone 按下按鈕
    microphone_startRecognizeOnceAsyncButton.addEventListener("click", function() {
        //設定Config
        speechConfig = SpeechSDK.SpeechTranslationConfig.fromSubscription(subscription, ServiceRegion);

        microphone_startRecognizeOnceAsyncButton.disabled = true;
        micorphone_resultsDivs.forEach(function(elem) {
            elem.innerHTML = "";
        });


        //設定來源語音種類
        speechConfig.speechRecognitionLanguage = micorphone_languageSourceOptions.value;
        let languageKeys = {};
        //設定目標文字種類
        micorphone_languageTargetOptions.forEach(function(langElem, index) {
            let language = langElem.value;
            languageKeys[language] = micorphone_resultsDivs[index];
            speechConfig.addTargetLanguage(language);
        });

        var audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

        recognizer = new SpeechSDK.TranslationRecognizer(speechConfig, audioConfig);
        recognizer.recognizeOnceAsync(
            function(result) {
                microphone_startRecognizeOnceAsyncButton.disabled = false;
                if (result.reason === SpeechSDK.ResultReason.TranslatedSpeech) {
                    for (var key in languageKeys) {
                        let translation = result.translations.get(key);
                        window.console.log(key + ": " + translation);
                        languageKeys[key].innerHTML += translation;
                    }
                }

                recognizer.close();
                recognizer = undefined;
            },
            function(err) {
                microphone_startRecognizeOnceAsyncButton.disabled = false;
                micorphone_resultsDiv[0].innerHTML += err;
                window.console.log(err);

                recognizer.close();
                recognizer = undefined;
            });
    });

    //file
    file_startRecognizeOnceAsyncButton = document.getElementById("file_startRecognizeOnceAsyncButton");
    phraseDiv = document.getElementById("phraseDiv");
    translation_filePicker = document.getElementById("translation_filePicker");

    file_languageSourceOptions = document.getElementById("file_languageSourceOptions");
    file_languageTargetOptions = [
        document.getElementById("file_languageTargetOptions1"),
        document.getElementById("file_languageTargetOptions2")
    ];
    file_resultsDivs = [
        document.getElementById("file_phraseDiv1"),
        document.getElementById("file_phraseDiv2")
    ];
    translation_filePicker.addEventListener("change", function() {
        audioFile = translation_filePicker.files[0];
        file_startRecognizeOnceAsyncButton.disabled = false;
    });

    //file 按下按鈕
    file_startRecognizeOnceAsyncButton.addEventListener("click", function() {

        //設定Config
        speechConfig = SpeechSDK.SpeechTranslationConfig.fromSubscription(subscription, ServiceRegion);
        
        console.log(subscription,ServiceRegion)

        file_startRecognizeOnceAsyncButton.disabled = true;
        file_resultsDivs.forEach(function(elem) {
            elem.innerHTML = "";
        });

        //設定來源語音種類
        speechConfig.speechRecognitionLanguage = file_languageSourceOptions.value;
        let languageKeys = {};
        //設定目標文字種類
        file_languageTargetOptions.forEach(function(langElem, index) {
            let language = langElem.value;
            languageKeys[language] = file_resultsDivs[index];
            speechConfig.addTargetLanguage(language);
        });


        //將上傳檔案
        var audioConfig = SpeechSDK.AudioConfig.fromWavFileInput(audioFile);
        recognizer = new SpeechSDK.TranslationRecognizer(speechConfig, audioConfig);
        recognizer.recognizeOnceAsync(
            function(result) {
                console.log(result)
                for (var key in languageKeys) {
                    console.log(languageKeys)
                    let translation = result.translations.get(key);
                    window.console.log(key + ": " + translation);
                    languageKeys[key].innerHTML += translation;
                }
                recognizer.close();
                recognizer = undefined;
            },
            function(err) {

                startRecognizeOnceAsyncButton.disabled = false;
                file_resultsDivs[0].innerHTML += err;
                window.console.log(err);
                recognizer.close();
                recognizer = undefined;
            });
    });

    if (!!window.SpeechSDK) {
        SpeechSDK = window.SpeechSDK;
        microphone_startRecognizeOnceAsyncButton.disabled = false;


        document.getElementById('translation_microphone').style.display = 'block';
        document.getElementById('translation_file').style.display = 'block';
    }
});