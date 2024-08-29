import streamlit as st
import psycopg2
import ollama
from psycopg2 import sql

st.logo("logo.png", link="https://www.enterprisedb.com/")
st.set_page_config(
        page_title="RAG",
        page_icon="logo.png",
        layout="wide",
    )
#if 'conn' not in st.session_state:
db_ip = st.sidebar.text_input('dbip', '')

if len(db_ip)>0:
    conn = psycopg2.connect(
                user="postgres",
                password="edb",
                host=db_ip,
                port=5432,  # The port you exposed in docker-compose.yml
                database="testdb"
            
            )
        #st.session_state['conn'] = conn
        #cur = st.session_state.conn.cursor()
        #st.session_state['cur'] = cur
    options=[]
    with conn.cursor() as cur:
        cur.execute(
           """SELECT table_name FROM information_schema.tables
           WHERE table_schema = 'public'"""
        )
        
        for row in cur.fetchall():
            options.append(row[0])
        cur.close()
    
    selected_dataset = st.sidebar.selectbox(
        "select dataset",
        options,
    )
    # Initialize chat history
    #message_history=[]
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
    
    #st.write(
    #        """
    #    <style>
    #        .st-emotion-cache-1wmy9hl {
    #            flex-direction: column-reverse;
    #        }
    #    </style>
    #    """ ,
    #        unsafe_allow_html=True,
    #    )
    debug_response=""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # Accept user input
    if user_question := st.chat_input("What's on your mind?"):
        
        # Add user message to chat history
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            st.markdown(user_question)
            #message_history.append({'role': 'user', 'content': user_question})
    
        with st.chat_message("assistant"):
            my_bar = st.progress(0, text="Searching the knowledgebase...")
            with my_bar: #st.spinner('Searching the knowledgebase...'):
                #st.session_state.debug = user_question
                query_embedding = ollama.embeddings(model="mxbai-embed-large", prompt=user_question)
                query_result=""
                with conn.cursor() as cur:
                    #st.session_state.cur = st.session_state.conn.cursor()
                    #pdf_edb
                    
                    
                    cur.execute(
                        sql.SQL("""SELECT id, content, 1-(embedding <=> %s::vector) DIST
                            FROM {}
                            WHERE (1-(embedding <=> %s::vector)) > 0.6
                            ORDER BY DIST DESC LIMIT 20;""",                        
                            ).format(sql.Identifier(selected_dataset)),[query_embedding["embedding"],query_embedding["embedding"],]
                    )
                    
                    
                    for row in cur.fetchall():
                        #print(f"ID: {row[0]}, CONTENT: {row[1]}, Cosine Similarity: {row[2]}")
                        query_result = query_result + "|" + row[1]
                        debug_response = debug_response + "****"+str(row[0])+"####" + str(row[2]) + ">>>>>" + row[1]
                        
                    debug_response = debug_response.replace('"','')
                    debug_response = debug_response.replace("'","")
                    debug_response = debug_response.replace(":","")
                    debug_response = debug_response.replace("\n","")
                    #st.session_state.cur.close()
                    conn.close()
                    #st.session_state.debug = st.session_state.debug+'\n'+query_result
                #print("*************************************************************************")
                #output = ollama.generate(
                #    model="llama3.1", # mistral
                #    prompt=f"Using this data: {user_question}. Respond to this prompt: {query_result}"
                #)
                tmp=[]
                #tmp.extend(st.session_state.messages[-2:])
                #tmp = st.session_state.messages.copy()
                tmp.append({"role": "user", "content": "Use this retrieved data:" + query_result + ". to answer this question: " + user_question})
                my_bar.progress(5, text="generating augmented response")
                output = ollama.chat(
                        model='llama3.1',
                        messages=tmp ,
                        stream=True,
                    )
                response = ""
                progress = 5
                for chunk in output:
                    #st.markdown(chunk['message']['content'], end='', flush=True)
                    response=response+chunk['message']['content']
                    progress=progress+1
                    my_bar.progress(min((100,progress)), text="streaming augmented response")
                #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                #print(output['response'])
                #print("__________________________________________________________________________")
                
                #response = output['response'] 
                #response = output['message']['content']
                st.session_state.messages.append({"role": "assistant", "content": response})
                #message_history.append({'role': 'assistant', 'content': response})
                
                my_bar.empty()
                st.markdown(response)
    
             
    #st.text_area("response",key="response",height=400)
    
    #prompt = st.chat_input("Say something",key="question")#,on_submit=update_response)
    
    #st.text_area("debug", key="debug",height=200)


    js2 = f"""
    <script>
        function debug(message_to_log){{
            if(message_to_log!='')
               console.log("EDB response "+message_to_log);
        }}
        
        debug("{debug_response}");
    </script>
    """
    
    st.components.v1.html(js2)


