import streamlit as st
import pymysql
import pathlib
import pandas as pd

session_username=st.session_state['username']
session_password=st.session_state['password']


db=pymysql.connect(host='localhost',user='root',password='',database='mhm')
cursor=db.cursor()

Sessions=st.sidebar.page_link("pages/therapists_sessions.py",label="Sessions",icon=":material/description:")
Progress=st.sidebar.page_link("pages/view_patients_progress.py",label="Patients Progress",icon=":material/acute:")
Chatbot=st.sidebar.page_link("pages/therapists_chatbot.py",label="Therapist Assistant AI",icon=":material/robot_2:")



if st.sidebar.button(label="Logout",use_container_width=True,key="back_to"):
   st.switch_page("Login_screen.py")


# Creating appointments table if it does not exist
try:
   create_appointments_table="""CREATE TABLE IF NOT EXISTS appointments(
   ID INT AUTO_INCREMENT PRIMARY KEY,
   patient_id INT REFERENCES patients_registration(ID),
   therapist_id INT REFERENCES therapists_registration(ID),
   appointment_date DATE NOT NULL,
   appointment_time datetime NOT NULL,
   status ENUM('booked','completed','cancelled') default 'booked',
   created_at TIMESTAMP NOT NULL,
   updated_at TIMESTAMP
   );"""
   cursor.execute(create_appointments_table)
   db.commit()
except Exception as e:
   st.error(f"There was an error creating the table named 'appointments': {e}")


# Creating sessions table if it does not exist - Updated to match actual table structure
try:
   create_session_table="""CREATE TABLE IF NOT EXISTS sessions(
   ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
   appointment_id INT DEFAULT NULL,
   therapist_id INT DEFAULT NULL,
   session_date DATE NOT NULL,
   session_notes TEXT,
   created_at TIMESTAMP NOT NULL,
   updated_at TIMESTAMP NULL DEFAULT NULL,
   status ENUM('pending','completed','cancelled') DEFAULT 'pending',
   session_time TIME NOT NULL,
   mood_rating INT DEFAULT NULL,
   anxiety_level INT DEFAULT NULL,
   depression_level INT DEFAULT NULL,
   stress_level INT DEFAULT NULL,
   sleep_quality INT DEFAULT NULL,
   energy_level INT DEFAULT NULL,
   social_interaction INT DEFAULT NULL,
   self_care INT DEFAULT NULL,
   primary_goal_progress INT DEFAULT NULL,
   secondary_goal_progress INT DEFAULT NULL,
   session_helpfulness INT DEFAULT NULL,
   homework_completion ENUM('not_assigned','not_completed','partially_completed','completed') DEFAULT 'not_assigned',
   exercise_days_week INT DEFAULT NULL,
   panic_attacks_count INT DEFAULT 0,
   medication_compliance ENUM('poor','fair','good','excellent') DEFAULT NULL,
   progress_notes TEXT,
   therapist_observations TEXT
   );"""
   cursor.execute(create_session_table)
   db.commit()
except Exception as e:
   st.error(f"There was an error creating the table named 'sessions': {e}")



def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/style.css")
load_css(css_path)


class MainPanel:
  def __init__(self):
     st.html(f"<H1 class='prompt'>WELCOME {str.upper(session_username)}</H1>")
     view_options=st.selectbox('Select',options=["View your appointments","View your session notes"])

     if view_options=="View your appointments":
       self.view_appointments()
     elif view_options=="View your session notes":
       self.view_session_notes()


  def view_appointments(self):
    fetch_therapist_id="SELECT ID FROM therapists_registration WHERE Username=%s"
    cursor.execute(fetch_therapist_id, (session_username,))
    therapist_id=cursor.fetchone()[0]


    try:
        
      view_all_appointments="""SELECT 
        pr.FNAME, 
        pr.LNAME, 
        a.appointment_date, 
        a.appointment_time, 
        a.status, 
        a.created_at, 
        a.updated_at 
    FROM 
        appointments a
    JOIN 
        patients_registration pr 
    ON 
        a.patient_id = pr.ID
    WHERE 
        a.therapist_id=%s;"""
      cursor.execute(view_all_appointments,(therapist_id,))
      result=cursor.fetchall()
      df=pd.DataFrame(result,columns=['Patients First Name','Patients Last Name','Appointment Date','Appointment Time','Status','Creation Date','Updation Date'])
      st.table(df)
      db.commit()
    except Exception as e:
       st.error(f"An error occurred: {e}")
       db.rollback()

  def view_session_notes(self):
    fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username=%s"
    cursor.execute(fetch_therapist_id, (session_username,))
    therapist_id = cursor.fetchone()[0]
    
    def view_all_sessions():
        try:
            fetch_all_sessions = """
            SELECT 
                s.ID,
                s.appointment_id,
                tr.username AS therapist_name,
                CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name,
                s.session_date,
                s.session_time,
                s.session_notes,
                s.status,
                s.mood_rating,
                s.anxiety_level,
                s.depression_level,
                s.stress_level,
                s.sleep_quality,
                s.energy_level,
                s.social_interaction,
                s.self_care,
                s.primary_goal_progress,
                s.secondary_goal_progress,
                s.session_helpfulness,
                s.homework_completion,
                s.exercise_days_week,
                s.panic_attacks_count,
                s.medication_compliance,
                s.progress_notes,
                s.therapist_observations,
                s.created_at,
                s.updated_at
            FROM sessions s
            JOIN therapists_registration tr ON s.therapist_id = tr.ID
            JOIN appointments a ON s.appointment_id = a.ID
            JOIN patients_registration pr ON a.patient_id = pr.ID
            WHERE s.therapist_id = %s
            ORDER BY s.session_date DESC, s.session_time DESC
            """
            
            cursor.execute(fetch_all_sessions, (therapist_id,))
            all_sessions_result = cursor.fetchall()
            
            if all_sessions_result:
                df = pd.DataFrame(all_sessions_result, columns=[
                    'Session ID', 
                    'Appointment ID', 
                    'Therapist Name',
                    'Patient Name',
                    'Session Date', 
                    'Session Time',
                    'Session Notes',
                    'Status',
                    'Mood Rating',
                    'Anxiety Level',
                    'Depression Level',
                    'Stress Level',
                    'Sleep Quality',
                    'Energy Level',
                    'Social Interaction',
                    'Self Care',
                    'Primary Goal Progress',
                    'Secondary Goal Progress',
                    'Session Helpfulness',
                    'Homework Completion',
                    'Exercise Days/Week',
                    'Panic Attacks Count',
                    'Medication Compliance',
                    'Progress Notes',
                    'Therapist Observations',
                    'Created At', 
                    'Updated At'
                ])
                
                # Display summary view first (key columns only)
                summary_columns = ['Session ID', 'Patient Name', 'Session Date', 'Session Time', 'Status', 'Mood Rating']
                st.subheader("Sessions Summary")
                st.dataframe(df[summary_columns], use_container_width=True)
                
                # Option to view detailed data
                if st.checkbox("Show Detailed View"):
                    st.subheader("Detailed Sessions Data")
                    st.dataframe(df, use_container_width=True)
                
                db.commit()
            else:
                st.info("NO SESSIONS NOTES AVAILABLE AS OF NOW")
                
        except Exception as e:
            st.error(f"There was an error {e}")
            db.rollback()
            
    def view_session_on_id(session_id):
        try:
            fetch_session_with_id = """
            SELECT 
                s.ID,
                s.appointment_id,
                tr.username AS therapist_name,
                CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name,
                s.session_date,
                s.session_time,
                s.session_notes,
                s.status,
                s.mood_rating,
                s.anxiety_level,
                s.depression_level,
                s.stress_level,
                s.sleep_quality,
                s.energy_level,
                s.social_interaction,
                s.self_care,
                s.primary_goal_progress,
                s.secondary_goal_progress,
                s.session_helpfulness,
                s.homework_completion,
                s.exercise_days_week,
                s.panic_attacks_count,
                s.medication_compliance,
                s.progress_notes,
                s.therapist_observations,
                s.created_at,
                s.updated_at
            FROM sessions s
            JOIN therapists_registration tr ON s.therapist_id = tr.ID
            JOIN appointments a ON s.appointment_id = a.ID
            JOIN patients_registration pr ON a.patient_id = pr.ID
            WHERE s.ID = %s AND s.therapist_id = %s
            """
            
            cursor.execute(fetch_session_with_id, (session_id, therapist_id))
            session_id_result = cursor.fetchone()
            
            if session_id_result:
                # Create a more readable display for individual session
                st.subheader(f"Session Details - ID: {session_id}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information:**")
                    st.write(f"Patient: {session_id_result[3]}")
                    st.write(f"Date: {session_id_result[4]}")
                    st.write(f"Time: {session_id_result[5]}")
                    st.write(f"Status: {session_id_result[7]}")
                    
                    st.write("**Mental Health Ratings:**")
                    st.write(f"Mood Rating: {session_id_result[8] or 'Not recorded'}")
                    st.write(f"Anxiety Level: {session_id_result[9] or 'Not recorded'}")
                    st.write(f"Depression Level: {session_id_result[10] or 'Not recorded'}")
                    st.write(f"Stress Level: {session_id_result[11] or 'Not recorded'}")
                
                with col2:
                    st.write("**Lifestyle Factors:**")
                    st.write(f"Sleep Quality: {session_id_result[12] or 'Not recorded'}")
                    st.write(f"Energy Level: {session_id_result[13] or 'Not recorded'}")
                    st.write(f"Social Interaction: {session_id_result[14] or 'Not recorded'}")
                    st.write(f"Self Care: {session_id_result[15] or 'Not recorded'}")
                    
                    st.write("**Progress & Goals:**")
                    st.write(f"Primary Goal Progress: {session_id_result[16] or 'Not recorded'}")
                    st.write(f"Secondary Goal Progress: {session_id_result[17] or 'Not recorded'}")
                    st.write(f"Session Helpfulness: {session_id_result[18] or 'Not recorded'}")
                
                st.write("**Additional Information:**")
                st.write(f"Homework Completion: {session_id_result[19] or 'Not assigned'}")
                st.write(f"Exercise Days/Week: {session_id_result[20] or 'Not recorded'}")
                st.write(f"Panic Attacks Count: {session_id_result[21] or 0}")
                st.write(f"Medication Compliance: {session_id_result[22] or 'Not recorded'}")
                
                # FIXED: Added proper labels with label_visibility="hidden"
                if session_id_result[6]:  # session_notes
                    st.write("**Session Notes:**")
                    st.text_area("Session Notes", session_id_result[6], height=100, disabled=True, label_visibility="hidden")
                
                if session_id_result[23]:  # progress_notes
                    st.write("**Progress Notes:**")
                    st.text_area("Progress Notes", session_id_result[23], height=100, disabled=True, key="progress", label_visibility="hidden")
                
                if session_id_result[24]:  # therapist_observations
                    st.write("**Therapist Observations:**")
                    st.text_area("Therapist Observations", session_id_result[24], height=100, disabled=True, key="observations", label_visibility="hidden")
                
                db.commit()
            else:
                st.info("NO SESSION FOUND WITH THIS ID")
                
        except Exception as e:
            st.error(f"There was an error {e}")
            db.rollback()

    with st.container(key="session_ID_input_container", border=True):
        st.html("<H1 style='text-align:center;'>PLEASE SELECT ONE OF THE OPTIONS</H1>")
        session_id_textbox = st.text_input(label="Please enter the session ID", placeholder="SESSION ID")
        fetch_session_id = st.button(label="GET SESSION DETAILS", use_container_width=True)
        if fetch_session_id and session_id_textbox:
            view_session_on_id(session_id_textbox)
    
    st.html("<H1 style='text-align: center;'>OR</H1>")
    view_all_sessions_button = st.button(label="VIEW ALL SESSIONS", use_container_width=True)
    
    # Initialize session state for showing all sessions
    if 'show_all_sessions' not in st.session_state:
        st.session_state.show_all_sessions = False
    
    # Set session state when button is clicked
    if view_all_sessions_button:
        st.session_state.show_all_sessions = True
    
    # Show sessions if button was clicked (persists across reruns)
    if st.session_state.show_all_sessions:
        view_all_sessions()


if __name__=="__main__":
  MP=MainPanel()