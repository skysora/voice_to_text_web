


// stop the stream when you want and save all chunks that you have
document.addEventListener("DOMContentLoaded", function() {

    var audio = new Audio();
    var ms = new MediaSource();
    var chunks = [];
    var stopBtn = document.getElementById("StopBtn");
    audio.src = URL.createObjectURL(ms);


    ms.addEventListener('sourceopen', function(e) {
        var sourceBuffer = ms.addSourceBuffer('audio/mpeg');
        var stream;

        function pump(stream){
            return stream.read().then(data => {
                chunks.push(data.value)

                sourceBuffer.appendBuffer(data.value);
            })
        };

        sourceBuffer.addEventListener('updateend', () => {
            pump(stream);
        }, false);

        fetch("http://stream001.radio.hu:443/stream/20160606_090000_1.mp3")
            .then(res=>pump(stream = res.body.getReader()))

        // audio.play()
    }, false);

    stopBtn.addEventListener("click", function () {
        console.log("------")
        var blob = new Blob(chunks)
        console.log(blob)
        // Create object url, append to link, trigger click to download
        // or saveAs(blob, 'stream.mp3') need: https://github.com/eligrey/FileSaver.js
    });
})