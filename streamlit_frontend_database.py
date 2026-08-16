import streamlit as st 
from langgraph_backend_database import chatbot , retreive_all_thread
from langchain_core.messages import HumanMessage , AIMessage
import uuid 

#  ---------------- utility Function ---------------------

def generate_thread_id():
   thread_id =  uuid.uuid4()
   return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable' : {'thread_id' : thread_id}})
    return state.values.get('messages',[])

# st.session_state -> dict ->
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retreive_all_thread()

add_thread(st.session_state['thread_id'])

#-------------side Bar -------------------

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversation')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        message = load_conversation(thread_id)

        temp_message = []

        for msg in message:
            if isinstance(msg , HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_message.append({'role':role,'content':msg.content[0]['text'] if isinstance(msg.content, list) else msg.content})

        st.session_state['message_history'] = temp_message


#---------- Main UI -------------------------------

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
       st.text(message['content']) 

user_input = st.chat_input('Type here')

if user_input:

    #first add the message to message history
    st.session_state['message_history'].append({'role' : 'user' , 'content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    Config = {'configurable' : {'thread_id' : st.session_state['thread_id']}}

    with st.chat_message("assistant"):

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=Config,
                stream_mode="messages"
            ):

                if isinstance(message_chunk, AIMessage):

                    if isinstance(message_chunk.content, list):

                        for item in message_chunk.content:

                            if isinstance(item, dict):
                                text = item.get("text", "")

                                if text:
                                    yield text

                    elif isinstance(message_chunk.content, str):

                        if message_chunk.content:
                            yield message_chunk.content


    ai_message = st.write_stream(ai_only_stream())



    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })