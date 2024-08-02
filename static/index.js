let recorder;
let audioChunks = [];

document.getElementById("record-btn").addEventListener("click", async () => {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/mp3" });
        audioChunks = [];

        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = document.getElementById("audio-playback");
        audio.src = audioUrl;
        audio.hidden = false;

        const formData = new FormData();
        formData.append("file", audioBlob, "recorded_audio.mp3");

        // Show user message immediately after recording
        const conversationDiv = document.querySelector(".conversation");
        const userMsgDiv = document.createElement("div");
        userMsgDiv.classList.add("user-msg");
        userMsgDiv.innerHTML =
          'آپ کا پیغام... <div class="loading-placeholder"><img src="static/loading.gif" alt="loading" /></div>';
        conversationDiv.appendChild(userMsgDiv);

        // Add a placeholder for the bot's response
        const botMsgDiv = document.createElement("div");
        botMsgDiv.classList.add("bot-msg", "loading-placeholder");
        botMsgDiv.innerHTML =
          'بوٹ جواب دے رہا ہے... <img src="static/loading.gif" alt="loading" />';
        conversationDiv.appendChild(botMsgDiv);
        conversationDiv.scrollTop = conversationDiv.scrollHeight;

        const transcriptionResponse = await fetch("/upload", {
          method: "POST",
          body: formData,
        });

        if (transcriptionResponse.ok) {
          const transcriptionResult = await transcriptionResponse.json();
          console.log(transcriptionResult); // Log the result to check its structure

          // Ensure result and its properties exist
          if (transcriptionResult && transcriptionResult.transcription) {
            // Update user message with transcription
            userMsgDiv.innerHTML = `<strong>آپ:</strong> ${transcriptionResult.transcription}`;

            // Fetch bot response
            const botResponse = await fetch("/bot_response", {
              method: "POST",
              body: JSON.stringify({
                transcription: transcriptionResult.transcription,
              }),
              headers: { "Content-Type": "application/json" },
            });

            if (botResponse.ok) {
              const result = await botResponse.json();
              if (result && result.response && result.audio_url) {
                // Update bot message with the actual response
                botMsgDiv.classList.remove("loading-placeholder");
                botMsgDiv.innerHTML = `
                  <strong>بوٹ:</strong> ${result.response}
                  <button class="speak-btn" data-audio-url="${result.audio_url}">
                    <i class="fas fa-volume-up"></i>
                  </button>
                `;

                // Hide the audio element
                const audioElement = new Audio(result.audio_url);
                let isPlaying = false;

                botMsgDiv
                  .querySelector(".speak-btn")
                  .addEventListener("click", function () {
                    if (isPlaying) {
                      audioElement.pause();
                    } else {
                      audioElement.play();
                    }
                    isPlaying = !isPlaying;
                  });

                conversationDiv.scrollTop = conversationDiv.scrollHeight;
              } else {
                botMsgDiv.innerHTML =
                  "بوٹ: جوابی پیغام حاصل کرنے میں دشواری ہوئی.";
              }
            } else {
              botMsgDiv.innerHTML =
                "بوٹ: جوابی پیغام حاصل کرنے میں دشواری ہوئی.";
            }
          } else {
            userMsgDiv.innerHTML =
              "آپ کا پیغام: ٹرانسکرپشن حاصل کرنے میں دشواری ہوئی.";
          }
        } else {
          userMsgDiv.innerHTML =
            "آپ کا پیغام: ٹرانسکرپشن حاصل کرنے میں دشواری ہوئی.";
        }
      };

      recorder.start();
      document.getElementById("record-btn").disabled = true;
      document.getElementById("stop-btn").disabled = false;
    } catch (err) {
      console.error("Error accessing microphone", err);
    }
  }
});

document.getElementById("stop-btn").addEventListener("click", () => {
  recorder.stop();
  document.getElementById("record-btn").disabled = false;
  document.getElementById("stop-btn").disabled = true;
});
