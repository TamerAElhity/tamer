import streamlit as st
import datetime
import os
import time
import psycopg2
import tkinter as tk
from tkinter import filedialog

st.logo("logo.png", link="https://www.enterprisedb.com/",icon_image="logo.png",)
st.set_page_config(
        page_title="RAG - Upload",
        page_icon="logo.png",
        layout="centered",
    )
db_ip = st.sidebar.text_input('dbip', 'localhost')

def db_connect(_force):
    if _force and 'conn' in st.session_state and st.session_state['conn'].closed==0:
        st.session_state['conn'].close()
    if _force or 'conn' not in st.session_state or st.session_state['conn'].closed ==1:
        st.session_state['conn'] = psycopg2.connect(user="postgres",password="edb",host=st.session_state['db_ip'],port=5432,database="testdb")
    return st.session_state['conn']
          
if 'db_ip' not in st.session_state:
    st.session_state['db_ip'] = db_ip
    db_connect(True)  
            
if st.session_state['db_ip'] != db_ip:
    st.session_state['db_ip'] = db_ip
    db_connect(True)
def datasets():
    options=[]
    with db_connect(False).cursor() as cur:        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        for row in cur.fetchall():
            options.append(row[0])
        cur.close()
    if len(options)>0:
        options.insert(0,"")
    return options  

datasets_options=[]
try:
    datasets_options = datasets()
except:
    db_connect(True)
    datasets_options = datasets()
existing_dataset_name = st.sidebar.selectbox("select dataset",datasets_options,0)
new_dataset_name = st.sidebar.text_input(", or new dataset",)
if db_ip.strip() != "" and (
        (existing_dataset_name and existing_dataset_name.strip() != "") 
        or new_dataset_name.strip() != ""):
    truncate = st.sidebar.checkbox('Truncate')
    # Folder picker button
    #st.write('Please select a folder:')
    clicked = st.button('Select a folder')
    if clicked: 
        dataset_name=''
        if existing_dataset_name and existing_dataset_name.strip() != "":
            dataset_name = existing_dataset_name
        elif new_dataset_name and new_dataset_name.strip() != "":
            dataset_name = new_dataset_name
        else:
            st.sidebar.write(":red[select either existing or new dataset name]")
        if dataset_name.strip() != "":
            # Set up tkinter
            root = tk.Tk()
            root.withdraw()        
            # Make folder picker dialog appear on top of other windows
            root.wm_attributes('-topmost', 1)
            dirname = filedialog.askdirectory(master=root) # st.text_input('Selected folder:', filedialog.askdirectory(master=root))
            if dirname.strip() != "" :    
                with st.spinner('processing files in ' + dirname + '...'):     
                    file_list = os.listdir(dirname)
                    
                
                    for filename in file_list:
                        st.write(f"PostgresAI query \n\n :green[select process_file ('{dataset_name}','{dirname}','{filename}',{truncate})]")                        
                        time0=time.time()
                        with db_connect(False).cursor() as cur:
                            cur.execute(f"select process_file ('{dataset_name}','{dirname}','{filename}',{truncate})")
                            st.write(f"processing file time {time.time()-time0:.2f}")                          
                            cur.close()
                            #conn.close()
                        db_connect(False).commit()
                    #db_connect(False).close()
                    st.success("Done!")


