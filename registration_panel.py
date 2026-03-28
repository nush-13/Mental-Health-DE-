import streamlit as st
import pymysql
import pathlib

db=pymysql.connect(host='localhost',user='root',password='',database='mhm')
cursor=db.cursor()

try:
    cursor.execute("""CREATE TABLE IF NOT EXISTS admin_registration
                   (ID INT AUTO_INCREMENT PRIMARY KEY, 
                   Fname VARCHAR(60) NOT NULL, 
                   Lname VARCHAR(60) NOT NULL,
                   MobileNumber numeric(10,0) NOT NULL, 
                   Email VARCHAR(255) NOT NULL,
                   username VARCHAR(60) NOT NULL,
                   password VARCHAR(60) NOT NULL);
                   """)
    db.commit()
except Exception as e:
    st.error(e)

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path=pathlib.Path("assets/style.css")
load_css(css_path)



class RegistrationPanel:
    def __init__(self):
        st.markdown("<H1 style='text-align: center;'>REGISTRATION PANEL</H1>",unsafe_allow_html=True)

        with st.form(key="forms"):
            col1,col2=st.columns(2)
            Fname=col1.text_input("First Name",placeholder="First Name")
            Lname=col2.text_input("Last Name",placeholder="Last Name")
            MobileNumber=st.text_input("Mobile Number",placeholder="Mobile Number")
            Email=st.text_input("Email",placeholder="Email")
            username=st.text_input("Username",placeholder="Username")
            c1,c2=st.columns(2)
            password=c1.text_input("Password",placeholder="Password")
            confirm_password=c2.text_input("Confirm Password",placeholder="Confirm Password",type="password")
            if st.form_submit_button("Submit",use_container_width=True):
                self.RegisterAccount(Fname,Lname,MobileNumber,Email,username,password,confirm_password)

        with st.container():
            st.markdown("---")
            st.markdown("<H1 style='text-align: center;'>OR</H1>",unsafe_allow_html=True)
            st.markdown("---")
            if st.button("BACK TO LOGIN",icon="⬅️",use_container_width=True,key="back_to"):
                st.switch_page("Login_screen.py")


    def RegisterAccount(self,Fname,Lname,MobileNumber,Email,username,password,confirm_password):
        if not Fname or not Lname:
            st.error("First Name and Last Name are required.")
            return
        if not MobileNumber or not(MobileNumber.isdigit()) or len(MobileNumber)!=10:
            st.error("Please enter a valid mobile number.")
            return
        if not Email or '@' not in Email or '.' not in Email:
            st.error("Please enter a valid email address")
            return
        if not username or not password:
            st.error("Username and Password are required.")
            return
        if username==password:
            st.error("Username and password must not be the same")
            return
        if password!=confirm_password:
            st.error("Passwords do not match. Please re-confirm the password by entering again")
            return
        
        verify_username_query="SELECT Username FROM verified_admins WHERE Username=%s"
        cursor.execute(verify_username_query, (username,))
        verify_username_result=cursor.fetchone()
        if verify_username_result:
            st.error("Username already exists. Please choose a different one.")
            return
        else:
            try:
                register_query="INSERT INTO admin_registration(Fname,Lname,MobileNumber,Email,username,password) VALUES(%s,%s,%s,%s,%s,%s)"
                cursor.execute(register_query, (Fname,Lname,MobileNumber,Email,username,password))
                result=cursor.rowcount
                if result>0:
                    st.success("Registration successful. Please wait for admin approval.")
                    db.commit()
                else:
                    st.error("Failed to register. Please try again.")
                    db.rollback()
            except Exception as e:
                st.error(f"an error occured: {e}")
                db.rollback()
                
if __name__=="__main__":
    RP=RegistrationPanel()