import React, { useState } from 'react';
import Draggable from 'react-draggable';
import { ResizableBox } from 'react-resizable';
import html2canvas from 'html2canvas';
import axios from 'axios';
import ls from './JinnInterface.less';
// import { SERVER_URL } from '../../../../../primitives/TypeScript/Constants/globals';
import 'react-resizable/css/styles.css'; // Import the styles for react-resizable

const isDev: boolean = true;
const SERVER_URL: string = isDev ? 'http://localhost:3001' : 'https://launch-server.make-print.com';

export default function JinnInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [screenshotDataUrl, setScreenshotDataUrl] = useState(null);

  const sendMessage = async () => {
    if (input.trim()) {
      try {
        setLoading(true);

        // Add a border to indicate screenshot capture
        document.body.style.border = "5px solid #AA00FF";

        // Capture the screenshot
        const screenshotCanvas = await html2canvas(document.body);
        const screenshotDataUrl = screenshotCanvas.toDataURL('image/png');

        // Remove the border after capturing the screenshot
        document.body.style.border = "none";

        // Set the screenshot data URL to state for inspection
        setScreenshotDataUrl(screenshotDataUrl);

        // Prepare and send the request to the backend
        axios.defaults.baseURL = SERVER_URL + '/jinn';
        const response = await axios.post('/predict', {
          prompt: input,
          screenshotDataUrl,
        });

        const predictions = response.data.predictions;

        // Update the messages
        setMessages([...messages, { from: 'user', text: input }, { from: 'ai', text: predictions[0] }]);
        setInput('');
        setLoading(false);
      } catch (error) {
        console.error('Error sending message:', error);
        setLoading(false);
      }
    }
  };

  return (
    <Draggable>
      <div className={ls.chatContainer}>
        <ResizableBox
          width={800}
          height={800}
          minConstraints={[800, 800]}
          maxConstraints={[1600, 1600]}
          className={ls.resizableBox}
        >
          <div className={ls.chatHeader}>Jinn</div>
          <div className={ls.chatMessages}>
            {messages.map((msg, index) => (
              <div key={index} className={msg.from === 'user' ? ls.userMessage : ls.aiMessage}>
                {msg.text}
              </div>
            ))}
            {loading && <div className={ls.loading}>Loading...</div>}
          </div>
          <div className={ls.chatInputContainer}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className={ls.chatInput}
              placeholder="Type your message..."
            />
            <button onClick={sendMessage} className={ls.sendButton}>Send</button>
          </div>
          {screenshotDataUrl && (
            <div className={ls.screenshotContainer}>
              <h3>Captured Screenshot:</h3>
              <img src={screenshotDataUrl} height="auto" alt="Screenshot" className={ls.screenshot} />
            </div>
          )}
        </ResizableBox>
      </div>
    </Draggable>
  );
}
