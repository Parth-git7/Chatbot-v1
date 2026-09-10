from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition

from gmail_authenticator import get_gmail_service
import base64
from email.message import EmailMessage
import requests
import sqlite3
import os


load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

###################### Define - TOOLS ##########################################
search_tool = DuckDuckGoSearchRun(region = 'us-en')


@tool
def calculator(first_num: float, second_num: float, operation : str) -> dict :
    """ Performs basic arithmetic operation on two numbers        
    Supported Operation: add, sub, mul, div"""
    # the above string thing is important for the llm to know what this tool is meant to do and how

    try :
        if operation == 'add' :
            result = first_num + second_num 
        elif operation == 'sub' :
            result = first_num - second_num
        elif operation == 'mul' :
            result = first_num * second_num
        elif operation == 'div' :
            if second_num != 0 :
                result =  first_num / second_num 
            else :
                return {"error": "Division by zero is not allowed"}

        return {'first_num' : first_num, 'second_num' : second_num, 'operation' : operation, 'result' : result}
    except Exception as e :
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    r = requests.get(url)
    return r.json()


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email using Gmail.

    Args:
        to: Email address of the recipient.
        subject: Subject of the email.
        body: Content of the email.
    """

    try:
        service = get_gmail_service()

        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        create_message = {
            "raw": encoded_message
        }

        service.users().messages().send(
            userId="me",
            body=create_message
        ).execute()

        return "Email sent successfully."

    except Exception as e:
        return f"Failed to send email: {str(e)}"


tool_names = {
    "get_stock_price": "Fetching stock price",
    "calculator": "Calculating",
    "send_email": "Sending email",
    "duckduckgo_search": "Searching the web"
}

####################### define STATE ############################################
class chat_state(TypedDict) :
    messages : Annotated[list[BaseMessage], add_messages]


################## initialize model ##########################################
model = ChatOllama(model = 'qwen2.5:7b')
# model = ChatOpenAI(model = 'gpt-5.4-nano')


###################### bind model with tools ###################################
tools = [search_tool, calculator, get_stock_price, send_email]
model_with_tools = model.bind_tools(tools)


################### define nodes ###########################################
def chat_node(state : chat_state) -> chat_state :
    response = model_with_tools.invoke(state['messages'])
    return {'messages' : [response]}

tool_node = ToolNode(tools) 


##################### connect to database ##############################
connection = sqlite3.connect(database = 'chatbot.db', check_same_thread = False)
checkpointer = SqliteSaver(conn = connection)


####################### make graph #####################################
graph = StateGraph(chat_state)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition) 
## tools_condition inbuilt function check if any tool calls are there and returns exactly 'tools' if any
## else it returns '__end__' so we don't need to create and edge pointing to end 
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer = checkpointer)


################################################################
def retrieve_all_threads() :
    all_threads = set()
    for checkpoint in checkpointer.list(None) :
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)


####################### Testing code ##########################
# thread_id = "parth_chat_2"
# config= {'configurable' : {'thread_id' : thread_id}}

# # response = chatbot.invoke({'messages': [HumanMessage("What is the stock price of coca cola and email it as a proposal to buy 50 stocks to '7parth2006@gmail.com'")]}, config = config)
# response = chatbot.invoke({'messages': [HumanMessage("Send email to '7parth2006@gmail.com' advertising about coca cola stocks")]}, config = config)

# print(response['messages'][-1].content)




# for message_chunk, meta_data in chatbot.stream(
#     {"messages" : [HumanMessage("write something on cockatiels")]},
#     config= {'configurable' : {'thread_id' : thread_id}},
#     stream_mode= 'messages') :
    
#     if message_chunk.content :
#         print(message_chunk.content, end = '', flush= True)



# print(chatbot.get_state(config= {'configurable' : {'thread_id' : thread_id}}))
