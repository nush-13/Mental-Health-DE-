import streamlit as st
import pymysql
import time as t
import pathlib

db=pymysql.connect(host='localhost',user='root',password='',database='mhm')
cursor=db.cursor()
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verified_admins (
            ID INT AUTO_INCREMENT PRIMARY KEY, 
            Fname VARCHAR(60) NOT NULL, 
            Lname VARCHAR(60) NOT NULL, 
            MobileNumber NUMERIC(10,0) NOT NULL, 
            Email VARCHAR(255) NOT NULL, 
            Username VARCHAR(60) UNIQUE NOT NULL, 
            Password VARCHAR(60) NOT NULL
        );
    """)
    db.commit()
except Exception as e:
    st.error(f"Error while creating table: {e}")


#function to load CSS from 'assets' folder
def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path=pathlib.Path("assets/style.css")
load_css(css_path)


class LoginPanel:
    def __init__(self):
        st.markdown("<H1 style='text-align: center;' class='prompt'>LOGIN PANEL</H1>",unsafe_allow_html=True)
        with st.form(key='login-form'):
            user_type=st.selectbox("Select",options=['Admin','Therapist','Patient'])
            username=st.text_input("Username",placeholder="Username")
            password=st.text_input("Password",placeholder="Password",type="password")
            if st.form_submit_button("Login",use_container_width=True):
                self.validate_login(username,password,user_type)

        with st.container():
            st.markdown("---")
            st.markdown("<H1 style='text-align: center;'>OR</H1>",unsafe_allow_html=True)
            st.markdown("---")
            if st.button("REGISTER ADMIN",use_container_width=True,key='back_to'):
                st.switch_page("pages/registration_panel.py")
        
    def validate_login(self, username, password,user_type):
        if not username or not password:
            st.error("Please enter both username and password.")
            return
        
        if user_type=='Admin':
            try:
                login_query="SELECT * FROM verified_admins WHERE username=%s and password=%s"
                cursor.execute(login_query, (username, password))
                result=cursor.fetchone()
                if result:
                    st.session_state['username']=username
                    st.session_state['password']=password
                    st.success("Login successful.")
                    progress=st.progress(0)
                    for i in range(100):
                        t.sleep(0.01)
                        progress.progress(i+1)
                    st.switch_page("pages/app.py")
                    db.commit()
                else:
                    t.sleep(1)
                    st.error("Invalid username or password.")
            except Exception as e:
                st.error(f"Error while validating login: {e}")
                db.rollback()
        
        if user_type=='Therapist':
            try:
                therapist_login_query="SELECT * from therapists_registration WHERE Username=%s and Password=%s"
                cursor.execute(therapist_login_query,(username,password))
                result=cursor.fetchone()
                if result:
                    st.session_state['username']=username
                    st.session_state['password']=password
                    st.success('Login Succesfull')
                    progress=st.progress(0)
                    for i in range(100):
                        t.sleep(0.01)
                        progress.progress(i+1)
                    st.switch_page('pages/therapist_panel.py')
                    db.commit()                    
                else:
                    st.error('Invalid username or password')
            
            except Exception as e:
                st.error(f"Error while validating login: {e}")
                return
            
        if user_type=='Patient':
            try:
                patient_login_query="SELECT * from patients_registration WHERE Username=%s and Password=%s"
                cursor.execute(patient_login_query,(username,password))
                result=cursor.fetchone()
                if result:
                    st.session_state['username']=username
                    st.session_state['password']=password
                    st.success('Login Succesfull')
                    progress=st.progress(0)
                    for i in range(100):
                        t.sleep(0.01)
                        progress.progress(i+1)
                    st.switch_page('pages/patient_panel.py')
                    db.commit()
                else:
                    st.error("Invalid Username or Password")
            except Exception as e:
                st.error(f"Error while validating login: {e}")
                return        
        
        
        
            st.empty()
if __name__=="__main__":
    LP=LoginPanel()
