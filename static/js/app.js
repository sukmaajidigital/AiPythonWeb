const chatContainer = document.getElementById("chatContainer");
const queryInput = document.getElementById("queryInput");
const responseAudio = document.getElementById("responseAudio");

const appendMessage = (message, type) => {
  const div = document.createElement("div");
  const now = new Date();
  const formattedDate = now.toLocaleString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  div.className = `chat-message ${type}-message d-flex flex-column`;

  const chatBubble = document.createElement("div");
  chatBubble.className = "chat-bubble";
  chatBubble.innerText = message;

  const chatMeta = document.createElement("div");
  chatMeta.className = "chat-meta";
  chatMeta.innerText = type === "user" ? `You • ${formattedDate}` : `Bot • ${formattedDate}`;

  div.appendChild(chatBubble);
  div.appendChild(chatMeta);

  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
};

const playAudio = (audioPath) => {
  responseAudio.src = audioPath;
  responseAudio.hidden = false;
  responseAudio.load(); // Memastikan audio dimuat ulang
  responseAudio.play();
};

document.getElementById("sendQuery").addEventListener("click", async () => {
  const query = queryInput.value;
  if (!query) {
    alert("Masukkan teks terlebih dahulu!");
    return;
  }

  appendMessage(query, "user");
  queryInput.value = "";

  if (query.includes("buka")) {
    const app_name = query.replace("buka", "").trim();
    open_application(app_name);
  } else {
    const response = await fetch("/process-query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();
    appendMessage(data.response, "bot");

    if (data.audio_path) {
      playAudio(`/get-audio/${data.audio_path.split("/").pop()}`);
    }
  }
});

document.getElementById("startVoice").addEventListener("click", async () => {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "id-ID";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = async (event) => {
    const speechResult = event.results[0][0].transcript.toLowerCase();
    appendMessage(speechResult, "user");
    queryInput.value = speechResult;

    if (speechResult.includes("buka")) {
      const app_name = speechResult.replace("buka", "").trim();
      open_application(app_name);
    } else {
      const response = await fetch("/process-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: speechResult }),
      });

      const data = await response.json();
      appendMessage(data.response, "bot");

      if (data.audio_path) {
        playAudio(`/get-audio/${data.audio_path.split("/").pop()}`);
      }
    }
  };

  recognition.onerror = (event) => {
    alert("Terjadi kesalahan saat menangkap suara.");
  };

  recognition.start();
});

const open_application = (app_name) => {
  fetch("/open-application", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ app_name }),
  })
    .then((response) => response.json())
    .then((data) => {
      appendMessage(data.response, "bot");
      if (data.audio_path) {
        playAudio(`/get-audio/${data.audio_path.split("/").pop()}`);
      }
    });
};
