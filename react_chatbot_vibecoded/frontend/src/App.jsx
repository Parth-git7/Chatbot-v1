import { useState } from "react";
import "./App.css";


function App() {

  // Current active conversation ID
  const [threadId, setThreadId] = useState(
    crypto.randomUUID()
  );


  // All conversations stored locally in React
  const [chatThreads, setChatThreads] = useState([]);


  // Messages currently displayed
  const [messages, setMessages] = useState([]);


  // Text currently inside the input
  const [userInput, setUserInput] = useState("");


  // Loading state
  const [isLoading, setIsLoading] = useState(false);



  // -----------------------------
  // CREATE NEW CHAT
  // -----------------------------

  function newChat() {

    const newThreadId = crypto.randomUUID();

    setThreadId(newThreadId);

    setMessages([]);

  }



  // -----------------------------
  // SEND MESSAGE
  // -----------------------------

  async function sendMessage() {

    if (!userInput.trim()) {
      return;
    }


    const message = userInput;


    // Show user message immediately

    setMessages((previousMessages) => [

      ...previousMessages,

      {
        role: "user",
        content: message
      }

    ]);


    // Clear input

    setUserInput("");


    // Add current conversation to sidebar

    setChatThreads((previousThreads) => {

      const threadExists = previousThreads.some(
        (thread) => thread.id === threadId
      );


      if (threadExists) {
        return previousThreads;
      }


      return [

        {
          id: threadId,
          title: message
        },

        ...previousThreads

      ];

    });


    setIsLoading(true);


    try {

      // Send message to FastAPI

      const response = await fetch(
        "http://localhost:8000/chat",
        {

          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({

            message: message,

            thread_id: threadId

          })

        }
      );


      if (!response.ok) {
        throw new Error("Failed to get response");
      }


      const data = await response.json();


      // Add AI response

      setMessages((previousMessages) => [

        ...previousMessages,

        {
          role: "assistant",
          content: data.response
        }

      ]);

    }

    catch (error) {

      console.error(error);


      setMessages((previousMessages) => [

        ...previousMessages,

        {
          role: "assistant",
          content: "Sorry, something went wrong."
        }

      ]);

    }

    finally {

      setIsLoading(false);

    }

  }



  // -----------------------------
  // LOAD OLD CONVERSATION
  // -----------------------------

  async function loadConversation(id) {

    setThreadId(id);


    try {

      const response = await fetch(
        `http://localhost:8000/conversation/${id}`
      );


      const data = await response.json();


      setMessages(data.messages);

    }

    catch (error) {

      console.error(error);

    }

  }



  // -----------------------------
  // HANDLE ENTER KEY
  // -----------------------------

  function handleKeyDown(event) {

    if (event.key === "Enter" && !event.shiftKey) {

      event.preventDefault();

      sendMessage();

    }

  }



  // -----------------------------
  // UI
  // -----------------------------

  return (

    <div className="app">


      {/* =========================
          SIDEBAR
      ========================= */}

      <aside className="sidebar">


        <div className="sidebar-header">

          <h2>🤖 LangGraph AI</h2>

        </div>


        <button
          className="new-chat-button"
          onClick={newChat}
        >

          + New Chat

        </button>


        <div className="conversation-section">

          <p className="conversation-title">
            My Conversations
          </p>


          {chatThreads.length === 0 && (

            <p className="no-chats">
              No conversations yet
            </p>

          )}


          {chatThreads.map((thread) => (

            <button

              key={thread.id}

              className={
                thread.id === threadId
                  ? "conversation active"
                  : "conversation"
              }

              onClick={() =>
                loadConversation(thread.id)
              }

            >

              {thread.title.length > 30
                ? thread.title.slice(0, 30) + "..."
                : thread.title
              }

            </button>

          ))}

        </div>


      </aside>



      {/* =========================
          MAIN CHAT AREA
      ========================= */}

      <main className="chat-container">


        {/* HEADER */}

        <div className="chat-header">

          <h2>LangGraph Chatbot</h2>

          <p>
            Powered by LangGraph
          </p>

        </div>



        {/* MESSAGES */}

        <div className="messages-container">


          {messages.length === 0 && (

            <div className="welcome-screen">

              <h1>How can I help you?</h1>

              <p>
                Start a conversation with your AI assistant.
              </p>

            </div>

          )}



          {messages.map((message, index) => (

            <div

              key={index}

              className={`message-row ${message.role}`}

            >


              <div className="message">


                <div className="message-role">

                  {message.role === "user"
                    ? "You"
                    : "AI Assistant"
                  }

                </div>


                <div className="message-content">

                  {message.content}

                </div>


              </div>


            </div>

          ))}



          {isLoading && (

            <div className="message-row assistant">

              <div className="message loading-message">

                <div className="message-role">
                  AI Assistant
                </div>

                <div className="message-content">

                  Thinking...

                </div>

              </div>

            </div>

          )}


        </div>



        {/* INPUT */}

        <div className="input-container">


          <div className="input-box">


            <input

              value={userInput}

              onChange={(event) =>
                setUserInput(event.target.value)
              }

              onKeyDown={handleKeyDown}

              placeholder="Ask anything..."

              disabled={isLoading}

            />


            <button

              onClick={sendMessage}

              disabled={isLoading || !userInput.trim()}

            >

              Send

            </button>


          </div>


        </div>


      </main>


    </div>

  );

}


export default App;