import ollama
import streamlit as st
import psycopg2
import time
import json
import sys

def db_connect(_force):
    if _force and 'conn' in st.session_state and st.session_state['conn'].closed==0:
        st.session_state['conn'].close()
    if _force or 'conn' not in st.session_state or st.session_state['conn'].closed ==1:
        st.session_state['conn'] = psycopg2.connect(user="postgres",password="edb",host=st.session_state['db_ip'],port=5432,database="testdb")
    return st.session_state['conn']   
    


def datasets():
    datasets_options=[]
    try:
        with db_connect(False).cursor() as cur:        
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            for row in cur.fetchall():
                datasets_options.append(row[0])
            cur.close()
    except:
        db_connect(True)
        return datasets()
    if len(datasets_options)>0:
        datasets_options.insert(0,"")
    return datasets_options   
    
def ollama_models():
    options=[]
    ollamamodels = ollama.list()
    for model in ollamamodels['models']:
        if model['details']['quantization_level']!="F16" :
            options.append(model['model'])
    if len(options)>0:
        options.insert(0,"")
    #st.sidebar.write("llama3:8b")
    #st.sidebar.write("llama2:latest")
    #st.sidebar.write("llava-llama3:latest")
    
    #st.sidebar.write("mistral:latest")
    #st.sidebar.write("llama3:latest")
    return options

#def db_connect(_db_ip):
#    st.session_state['conn'] = psycopg2.connect(user="postgres",password="edb",host=_db_ip,port=5432,database="testdb")


def get_augemented_answer(_selected_dataset,_user_question,_selected_model,_question_to_model):
    _response=''
    st.sidebar.write(f"PG Query --> :green[select augmented_response('{_selected_dataset}','{_user_question.strip()}','{_selected_model}',{_question_to_model})]")
    
    with db_connect(False).cursor() as cur:
        time0 = time.time()
        cur.execute(f"select augmented_response ('{_selected_dataset}','{_user_question.strip()}','{_selected_model}',{_question_to_model})")
        
        time1=time.time()
        for row in cur.fetchall():
            row_json = json.loads(row[0])
            _response = f"{row_json['llm_response']} \n\n :red[{_selected_model} total time : {time1-time0:.2f} sec [ LLM time {row_json['llm_time']}, PG time {row_json['pg_time']})]]"
        cur.close()
    db_connect(False).close()
    return _response
    
def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)
        
st.logo("logo.png", link="https://www.enterprisedb.com/")
st.set_page_config(page_title="RAG - Retriever",page_icon="logo.png",layout="wide",)
st.markdown(
        """
    <style>
        .st-emotion-cache-1c7y2kd {
            flex-direction: row-reverse;
            text-align: right;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

db_ip = st.sidebar.text_input('db_ip', 'localhost')
if 'db_ip' not in st.session_state:
    st.session_state['db_ip'] = db_ip
    db_connect(True)  
            
if st.session_state['db_ip'] != db_ip:
    st.session_state['db_ip'] = db_ip
    db_connect(True)
    
if "messages" not in st.session_state:
    st.session_state.messages = []  

#st.sidebar.write(len(st.session_state.messages))
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

selected_dataset = st.sidebar.selectbox("select dataset",datasets(),)
selected_model = st.sidebar.selectbox("select model",ollama_models(),)  

st.sidebar.write(f"Model recommendations (:green[gemma2:2b , llama3.1:latest])")

question_to_model = st.sidebar.checkbox('Question to the model')
        
if db_connect(False).closed == 0:
    if (isinstance(selected_dataset,str) and (selected_dataset.strip() == "") or (selected_model.strip() == "") and isinstance(selected_model,str)):
        st.sidebar.write(f":red[please choose dataset and llm model]")
        
    if isinstance(selected_dataset,str) and selected_dataset.strip() != "" and isinstance(selected_model,str) and selected_model.strip() != "":
        # Accept user input
        if user_question := st.chat_input("What's on your mind?"):
            with st.chat_message("user"):                               
                # Display user message in chat message container
                st.write(user_question)   
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": user_question})              
            with st.chat_message("assistant"):
                with st.spinner('Searching the local knowledgebase ...'):                           
                    response = get_augemented_answer(selected_dataset,user_question,selected_model,question_to_model)                    
                # Display postgres response message in chat message container
                st.write_stream(stream_data(response))
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": response}) 

    

