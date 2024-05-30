import React, { useState } from 'react';
import Draggable from 'react-draggable';
import ls from './JinnInterface.less';

export default function JinnInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  console.log('JinnInterface rendering');

  const sendMessage = () => {
    if (input.trim()) {
      // Simulate sending message to the AI and receiving a response
      setMessages([...messages, { from: 'user', text: input }, { from: 'ai', text: 'Response from AI' }]);
      setInput('');
    }
  };

  return (
    <Draggable>
      <div className={ls.chatContainer}>
        <div className={ls.chatHeader}>Jinn</div>
        <div className={ls.chatMessages}>
          {messages.map((msg, index) => (
            <div key={index} className={msg.from === 'user' ? ls.userMessage : ls.aiMessage}>
              {msg.text}
            </div>
          ))}
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
      </div>
    </Draggable>
  );
}
