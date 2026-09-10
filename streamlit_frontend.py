import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, BaseMessage

CONFIG = {
        "configurable": {
            "thread_id": "chat-1"
        }
    }
# st.session_state -> dict -> session state is a dictionary 
if 'message_history' not in st.session_state :
    st.session_state['message_history'] = []


# maintaining a message history
message_history = []

# initialising and load the message history
for message in st.session_state['message_history'] :
    with st.chat_message(message['role']) :
        st.text(message['content'])

user_input = st.chat_input('Type here :')

if user_input :
    # adding to message history
    st.session_state['message_history'].append({'role' : 'user', 'content' : user_input})
    with st.chat_message('user') :
        st.text(user_input)

    response = chatbot.invoke({"messages" : [HumanMessage(user_input)]}, config = CONFIG)
    ai_message = response['messages'][-1].content

    st.session_state['message_history'].append({'role' : 'assistant', 'content' : user_input})
    with st.chat_message('assistant') :
        st.text(ai_message)

