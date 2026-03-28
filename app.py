import streamlit as st
import pymysql
import pathlib
import pandas as pd
import time as t


# Database connection
db = pymysql.connect(host='localhost', user='root', password='', database='mhm')
cursor = db.cursor()

session_username = st.session_state['username']
session_password = st.session_state['password']

# Sidebar navigation
Navigation = st.sidebar.selectbox("Navigate", options=["View", "Register admins","Register Therapists","Register Patient"], key="sidebar_navigation")
st.sidebar.page_link("pages/appointments.py",label="Appointments",icon='📆',use_container_width=True)



# Function to load custom CSS
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/style.css")
load_css(css_path)

current_date=pd.to_datetime('now')
#Updating appointments status when the app loads
try:
    update_appointment_on_start = """
    UPDATE appointments
    SET status='completed'
    WHERE created_at < %s AND status='booked' AND appointment_date < %s
    """
    cursor.execute(update_appointment_on_start, (current_date, current_date))
    db.commit()
except Exception as e:
    st.error(f"Error while updating appointments: {e}")









# ViewOption class for viewing registered admins
class ViewOption:
    def __init__(self):
        st.markdown(f"<h1 class='prompt'>Welcome {session_username.upper()}</h1>", unsafe_allow_html=True)

        with st.form(key='options_form'):
            options = st.selectbox("Options", options=["View registered admins","View All Therapists","View All Patients"])

            username = st.text_input("Username", placeholder="Enter your username: ")
            password = st.text_input("Password", placeholder="Enter your password: ", type="password")

            if st.form_submit_button("View", use_container_width=True):
                if username == session_username and password == session_password:
                    if options == "View registered admins":
                        self.view_registered_admins()
                    if options=="View All Therapists":
                        self.view_all_therapists()
                    if options=="View All Patients":
                        self.view_all_patients()
                else:
                    st.info("Please enter a valid username and password")

    def view_all_patients(self):
        try:
            query="SELECT Fname,Lname,MobileNumber,Gender,Email,Username FROM patients_registration"
            cursor.execute(query)
            result=cursor.fetchall()
            if result:
                df=pd.DataFrame(result,columns=['First Name','Last Name','Mobile Number','Gender','Email','Username'])
                st.table(df)
            else:
                st.info("No patients found")
            db.commit()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()


    def view_all_therapists(self):
        try:
            query="SELECT Fname,Lname,MobileNumber,Email,Username,status from therapists_registration"
            cursor.execute(query)
            result=cursor.fetchall()
            if result:
                df=pd.DataFrame(result,columns=['First Name','Last Name','Mobile Number','Email','Username','Status'])
                st.table(df)
            else:
                st.info("No therapists found.")
            db.commit()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()


    def view_registered_admins(self):
        try:
            query = "SELECT Fname, Lname, MobileNumber, Email, Username FROM verified_admins"
            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                df = pd.DataFrame(result, columns=['First Name', 'Last Name', 'Mobile Number', 'Email', 'Username'])
                st.table(df)
            else:
                st.info("No registered admins found.")
        except Exception as e:
            st.error(f"An error occurred: {e}")



# RegisterAdmin class for admin registration functionality
class RegisterAdmin:
    def __init__(self):
        st.markdown(f"<h1 class='prompt'>Welcome {session_username.upper()}</h1>", unsafe_allow_html=True)
        try:
            query = "SELECT ID, Fname, Lname, MobileNumber, Email, username FROM admin_registration"
            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                df = pd.DataFrame(result, columns=['ID', 'First Name', 'Last Name', 'Mobile Number', 'Email', 'Username'])
                st.table(df)
                self.ApproveAdminForm()
            else:
                st.info("No new admins to register at the moment")            
        except Exception as e:
            st.error(f"An error occurred: {e}")

    def ApproveAdminForm(self):
        with st.form('register-admin'):
            st.html("<H1 class='prompt-registration'>Register this admin</H1>")
            ID = st.text_input("Place the ID", placeholder="ID")
            if ID:
                query_details = "SELECT Fname, Lname, MobileNumber, Email, username, password FROM admin_registration WHERE ID=%s"
                cursor.execute(query_details, (ID,))
                result_details = cursor.fetchone()
                if result_details:
                    Fname, Lname, MobileNumber, Email, username, password = result_details
                    col1, col2 = st.columns(2)
                    first_name = col1.text_input("First Name", value=Fname, disabled=True)
                    last_name = col2.text_input("Last Name", value=Lname, disabled=True)
                    mobile_number = col1.text_input("Mobile Number", value=MobileNumber, disabled=True)
                    email = col2.text_input("Email", value=Email, disabled=True)
                    user_name = st.text_input("Username", value=username, disabled=True)
                    flag=0
                else:
                    st.info("No admin found with this ID")
                    flag=1
            if st.form_submit_button("Submit",use_container_width=True):
                if flag==0:
                    self.RegisterNewAdmin(ID, first_name, last_name, mobile_number, email, user_name, password)
                else:
                    st.info("Admin not found with this ID")
                    return

            
    def RegisterNewAdmin(self, ID, Fname, Lname, MobileNumber, Email, Username, Password):
        try:
            query = "INSERT INTO verified_admins(Fname, Lname, MobileNumber, Email, Username, Password) VALUES(%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (Fname, Lname, MobileNumber, Email, Username, Password))
            result = cursor.rowcount
            if result > 0:
                progress=st.progress(0)
                for i in range(100):
                    t.sleep(0.02)
                    progress.progress(i+1)
                st.success("Admin registered successfully.")
                db.commit()
                query_delete = "DELETE FROM admin_registration WHERE ID=%s"
                cursor.execute(query_delete, (ID,))
                db.commit()
                st.rerun(scope='app')
            else:
                st.info("An error occurred")
                db.rollback()
        except Exception as e:
            st.error(f"An error occurred: {e}")


class RegisterTherapist:
    def __init__(self):
        st.markdown(f"<h1 class='prompt'>Welcome {session_username.upper()}</h1>", unsafe_allow_html=True)
        
        CREATING_TABLE="""CREATE TABLE IF NOT EXISTS therapists_registration
        (
        ID INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
        Fname VARCHAR(60) NOT NULL,
        Lname VARCHAR(60) NOT NULL,
        MobileNumber numeric(10,0) NOT NULL,
        Email VARCHAR(255) NOT NULL,
        Username VARCHAR(60) NOT NULL UNIQUE,
        Password VARCHAR(60) NOT NULL,
        status ENUM('Available','Booked') NOT NULL default 'available'
        );"""
        cursor.execute(CREATING_TABLE)
        db.commit()

        with st.form('register-therapist',clear_on_submit=True):
            col1,col2=st.columns(2)
            Fname=col1.text_input("First Name",placeholder="First Name")
            Lname=col2.text_input("Last Name",placeholder="Last Name")
            MobileNumber=st.text_input("Mobile Number",placeholder="Mobile Number")
            Email=st.text_input("Email",placeholder="Email")
            Username=st.text_input("Username",placeholder="Username")
            Password=st.text_input("Password",placeholder="Password",type='password')
            ConfirmPassword=st.text_input("Confirm Password",placeholder="Confirm Password",type='password')
            st.form_submit_button("REGISTER THERAPIST",use_container_width=True,on_click=self.confirmTherapistRegistration(Fname,Lname,MobileNumber,Email,Username,Password,ConfirmPassword))


    def confirmTherapistRegistration(self,Fname,Lname,MobileNumber,Email,Username,Password,ConfirmPassword):
        if not(Fname) or not(Lname):
            st.error("First name and Last name are required.")
            return
        if not(MobileNumber) or not(MobileNumber.isdigit()) or len(MobileNumber)!=10:
            st.error("Invalid mobile number. Please enter a 10-digit number.")
            return
        if not(Email) or '@' not in Email or '.' not in Email:
            st.error("Invalid email format.")
            return
        if not(Username) or not(Password):
            st.error("Username and Password are required.")
            return
        if Username==Password:
            st.error("Username and Password should not be the same.")
            return
        if Password!=ConfirmPassword:
            st.error("Passwords do not match.")
            return
    
        try:
            register_therapist_query="INSERT INTO therapists_registration(Fname,Lname,MobileNumber,Email,Username,Password) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(register_therapist_query,(Fname,Lname,MobileNumber,Email,Username,Password))
            result=cursor.rowcount
            if result>0:
                st.success("Registration successful.")
                progess=st.progress(0)
                for i in range(100):
                    t.sleep(0.02)
                    progess.progress(i+1)
                db.commit()
            else:
                st.error("An error occurred.")
                db.rollback()
        except Exception as e:
            if e.args[0]==1062:
                st.error("Username already exists.")
            else:
                st.error(f"An error occurred: {e}")       
            db.rollback()

class RegisterPatient:
    def __init__(self):
        st.markdown(f"<h1 class='prompt'>Welcome {session_username.upper()}</h1>", unsafe_allow_html=True)
        
        CREATING_TABLE="""CREATE TABLE IF NOT EXISTS patients_registration
        (
        ID INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
        Fname VARCHAR(60) NOT NULL,
        Lname VARCHAR(60) NOT NULL,
        MobileNumber numeric(10,0) NOT NULL,
        Gender ENUM('male','female') NOT NULL,
        Email VARCHAR(255) NOT NULL,
        Username VARCHAR(60) NOT NULL UNIQUE,
        Password VARCHAR(60) NOT NULL
        );"""
        cursor.execute(CREATING_TABLE)
        db.commit()


        with st.form("patient_registration",clear_on_submit=True):
            col1,col2=st.columns(2)
            Fname=col1.text_input("First Name",placeholder="First Name")
            Lname=col2.text_input("Last Name",placeholder="Last Name")
            MobileNumber=st.text_input("Mobile Number",placeholder="Mobile Number")
            Gender=st.selectbox("Gender",["male","female"],placeholder="Select a gender",index=None)
            Email=st.text_input("Email",placeholder="Email")
            Username=st.text_input("Username",placeholder="Username")
            Password=st.text_input("Password",placeholder="Password",type='password')
            ConfirmPassword=st.text_input("Confirm Password",placeholder="Confirm Password",type='password')
            st.form_submit_button("Register Patient",use_container_width=True,on_click=self.confirmPatientRegistration(Fname,Lname,MobileNumber,Gender,Email,Username,Password,ConfirmPassword))

    def confirmPatientRegistration(self,Fname,Lname,MobileNumber,Gender,Email,Username,Password,ConfirmPassword):
        if not(Fname) or not(Lname):
            st.error("First name and Last name are required.")
            return
        if not(MobileNumber) or not(MobileNumber.isdigit()) or len(MobileNumber)!=10:
            st.error("Invalid mobile number. Please enter a 10-digit number.")
            return
        if not(Email) or '@' not in Email or '.' not in Email:
            st.error("Invalid email format.")
            return
        if not(Username) or not(Password):
            st.error("Username and Password are required.")
            return
        if Username==Password:
            st.error("Username and Password should not be the same.")
            return
        if Password!=ConfirmPassword:
            st.error("Passwords do not match.")
            return
        

        try:
            confirm_patient_registration="INSERT INTO patients_registration(Fname,Lname,MobileNumber,Gender,Email,Username,Password) VALUES(%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(confirm_patient_registration,(Fname,Lname,MobileNumber,Gender,Email,Username,Password))
            result=cursor.rowcount
            if result>0:
                st.success("Registration successful.")
                progress=st.progress(0)
                for i in range(100):
                    t.sleep(0.02)
                    progress.progress(i+1)
                db.commit()
            else:
                st.error("An error occurred.")
                db.rollback()

        except Exception as e:
            if e.args[0]==1062:
                st.error("Username already exists.")
            else:
                st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    if Navigation == "View":
        view = ViewOption()
    elif Navigation == "Register admins":
        registerAdmin = RegisterAdmin()
    elif Navigation=="Register Therapists":
        registerTherapist = RegisterTherapist()
    elif Navigation=="Register Patient":
        registerPatient=RegisterPatient()
db.close()
