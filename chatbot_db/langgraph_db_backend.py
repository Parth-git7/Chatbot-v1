from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

load_dotenv()

class chat_state(TypedDict) :
    messages : Annotated[list[BaseMessage], add_messages]

model = ChatOllama(model = 'qwen2.5:7b')
# model = ChatOpenAI(model = 'gpt-5.4-nano')


def chat_node(state : chat_state) -> chat_state :

    response = model.invoke(state['messages'])
    return {'messages' : [response]}


connection = sqlite3.connect(database = 'chatbot.db', check_same_thread = False)
checkpointer = SqliteSaver(conn = connection)

graph = StateGraph(chat_state)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)


chatbot = graph.compile(checkpointer= checkpointer)

def retrieve_all_threads() :
    all_threads = set()
    for checkpoint in checkpointer.list(None) :
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)


####################### Testing code ##########################
# thread_id = "parth_chat_1"
# config= {'configurable' : {'thread_id' : thread_id}}

# response = chatbot.invoke({'messages' : [HumanMessage("what is the poem you wrote actually about ?")]}, config = config)
# print(response)

# thread_id = "parth_chat_1"



# for message_chunk, meta_data in chatbot.stream(
#     {"messages" : [HumanMessage("write something on cockatiels")]},
#     config= {'configurable' : {'thread_id' : thread_id}},
#     stream_mode= 'messages') :
    
#     if message_chunk.content :
#         print(message_chunk.content, end = '', flush= True)



# print(chatbot.get_state(config= {'configurable' : {'thread_id' : thread_id}}))
