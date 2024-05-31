import React, { useState, useRef } from "react";
import Draggable from "react-draggable";
import { ResizableBox } from "react-resizable";
import { ReactMediaRecorder } from "react-media-recorder";
import { Circles } from 'react-loader-spinner';
import axios from "axios";
import ls from "./JinnInterface.less";
import "react-resizable/css/styles.css"; // Import the styles for react-resizable
// import aiIcon from './HvFZuUellR.webp'; // Import the AI icon image

const isDev = false;
const SERVER_URL = isDev
  ? "http://localhost:5000"
  : "https://launch-fc.make-print.com";

export default function JinnInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [frameDataUrl, setFrameDataUrl] = useState(null);
  const videoRef = useRef(null);

  const sendMessage = async (capturedFrameDataUrl) => {
    console.log("Sending message:", input);
    if (input.trim() && capturedFrameDataUrl) {
      try {
        setLoading(true);

        console.log("Calling axios.post");
        // Prepare and send the request to the backend
        const response = await axios.post(`${SERVER_URL}/jinn/predict`, {
          prompt: input,
          screenshotDataUrl: capturedFrameDataUrl,
        });

        console.log("Response from axios.post", response);

        const predictions = response.data.predictions;

        // Update the messages
        setMessages([
          ...messages,
          { from: "user", text: input },
          { from: "ai", text: predictions[0] },
        ]);
        setInput("");
        setLoading(false);
      } catch (error) {
        console.error("Error sending message:", error);
        setLoading(false);
      }
    }
  };

  const captureFrameAndSendMessage = () => {
    const video = videoRef.current;
    if (video) {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const frameData = canvas.toDataURL("image/jpeg");
      // console.log("Frame data:", frameData); // This log should now be visible
      setFrameDataUrl(frameData);
      sendMessage(frameData);
    }
  };

  return (
    <Draggable>
      <div className={ls.chatContainer}>
        <ResizableBox
          width={300}
          height={300}
          minConstraints={[300, 300]}
          maxConstraints={[800, 800]}
          className={ls.resizableBox}
        >
          <div className={ls.chatHeader}>Jinn</div>
          <div className={ls.chatMessages}>
            {messages.map((msg, index) => (
              <div
                key={index}
                className={msg.from === "user" ? ls.userMessage : ls.aiMessage}
              >
                {msg.from === "ai" && <img src='img/cad/HvFZuUellR.webp' alt="AI Icon" className={ls.aiIcon} />}
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className={ls.loading}>
                <Circles
                  height="80"
                  width="80"
                  color="#4fa94d"
                  ariaLabel="circles-loading"
                  wrapperStyle={{}}
                  wrapperClass=""
                  visible={true}
                />
              </div>
            )}
          </div>
          <div className={ls.chatInputContainer}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className={ls.chatInput}
              placeholder="Type your message..."
            />
            <button onClick={captureFrameAndSendMessage} className={ls.sendButton}>
              Send
            </button>
          </div>
          {frameDataUrl && (
            <div className={ls.screenshotContainer}>
              <h3>Captured Frame:</h3>
              <img
                src={frameDataUrl}
                height="auto"
                alt="Frame"
                className={ls.screenshot}
              />
            </div>
          )}
          <ReactMediaRecorder
            screen
            render={({ previewStream, startRecording, stopRecording }) => (
              <div>
                <video
                  autoPlay
                  muted
                  playsInline
                  ref={(video) => {
                    if (video) {
                      video.srcObject = previewStream;
                      videoRef.current = video;
                    }
                  }}
                />
                <button onClick={startRecording}>Start Recording</button>
                <button onClick={stopRecording}>Stop Recording</button>
              </div>
            )}
          />
        </ResizableBox>
      </div>
    </Draggable>
  );
}
