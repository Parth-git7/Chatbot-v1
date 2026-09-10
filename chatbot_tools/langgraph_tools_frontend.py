import streamlit as st
from langgraph_tools_backend import chatbot, retrieve_all_threads, tool_names
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
import uuid 

######################### UTILITY FUNCTIONS ###########################################
# thread generator 
def generate_thread_id() :
    thread_id = uuid.uuid4()
    return str(thread_id)         ## this should be in string as buttons expect strings and thread id should be in strings

# reset function for new chat
def reset_chat() :
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id) :
    if thread_id not in st.session_state['chat_threads'] :
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id) :
    state = chatbot.get_state(config = { "configurable": { "thread_id": thread_id}})
    return state.values.get('messages', [])


# st.session_state -> dict -> session state is a dictionary 
################### SETTING UP SESSION STATE #######################################

if 'message_history' not in st.session_state :
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state :
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state :
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])



############################### SIDE BAR #########################################
st.sidebar.title("LangGraph ChatBot")
if st.sidebar.button("New Chat") :
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    messages = load_conversation(thread_id)
    if messages :
        name = messages[0].content
    else : 
        name = "New Chat"
    if st.sidebar.button(name, key = thread_id) :
        
        st.session_state['thread_id'] = thread_id
        message_history = []
        temp_history = load_conversation(thread_id)

        for msg in temp_history :
            if isinstance(msg, HumanMessage) :
                message_history.append({'role' : 'user', 'content' : msg.content })
            else :
                message_history.append({'role' : 'assistant', 'content' : msg.content })

        st.session_state['message_history'] = message_history


######################  initialising and load the message history
for message in st.session_state['message_history'] :
    with st.chat_message(message['role']) :
        st.text(message['content'])

user_input = st.chat_input('Type here :')

if user_input :
    # adding to message history
    st.session_state['message_history'].append({'role' : 'user', 'content' : user_input})
    with st.chat_message('user') :
        st.text(user_input)

    
    CONFIG = {
        "configurable": {
            "thread_id": st.session_state['thread_id']
        }
    }
    # st.session_state['message_history'].append({'role' : 'assistant', 'content' : user_input})
    # with st.chat_message('assistant') :
    with st.chat_message("assistant"):

        with st.status("🤖 Agent working...", expanded=True) as status:

            final_response = None

            for chunk in chatbot.stream(
                {"messages": [HumanMessage(user_input)]},
                config=CONFIG,
                stream_mode="updates"
            ):

                for node_name, node_output in chunk.items():

                    if node_name == "chat_node":

                        for msg in node_output.get("messages", []):

                            if getattr(msg, "tool_calls", None):

                                for tool_call in msg.tool_calls:

                                    name = tool_call["name"]

                                    label = tool_names.get(
                                        name,
                                        f"🔧 {name}"
                                    )

                                    st.write(f"🔄 {label}")

                            elif msg.content:

                                final_response = msg.content

                    elif node_name == "tools":

                        for msg in node_output.get("messages", []):

                            name = getattr(msg, "name", "")

                            label = tool_names.get(
                                name,
                                f"🔧 {name}"
                            )

                            st.write(f"✅ {label}")

            status.update(
                label="✅ Completed",
                state="complete",
                expanded=False
            )

        st.write(final_response)

    st.session_state['message_history'].append({
            'role': 'assistant',
            'content': final_response
        })
