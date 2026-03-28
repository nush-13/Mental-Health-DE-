import streamlit as st
import pymysql
import pandas as pd
import pathlib
import time as t
import os
from fpdf import FPDF
from fpdf.enums import XPos,YPos
from datetime import datetime

db=pymysql.connect(host='localhost',user='root',password='',database='mhm')
cursor=db.cursor()

session_username=st.session_state['username']


appointments_table_query="""CREATE TABLE IF NOT EXISTS appointments
    (ID INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT REFERENCES patients_registration(ID),
    therapist_id INT REFERENCES therapists_registration(ID),
    appointment_date DATE NOT NULL,
    appointment_time DATETIME NOT NULL,
    status ENUM('booked','completed','cancelled') default 'booked',
    created_at TIMESTAMP NOT NULL, 
    updated_at TIMESTAMP
    );
    """
try:
    cursor.execute(appointments_table_query)
    db.commit()
except Exception as e:
    st.error(f"Error while creating table: {e}")
    db.rollback()

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

css_path=pathlib.Path("assets/style.css")
load_css(css_path)









Appointment_options=st.sidebar.selectbox("Options",options=['View Appointments','Book Appointment','Update Appointments'])
main_panel=st.sidebar.page_link("pages/app.py",label="Home :material/home:",use_container_width=True)

class ViewAppointments:
    def __init__(self):
        st.markdown(f"<H1 class='prompt'>WELCOME {session_username.upper()}</H1>",unsafe_allow_html=True)
        ViewingOptions=st.selectbox("View Options",options=['Search An Appointment'])
        
        
        if ViewingOptions=='Search An Appointment':
            self.search_appointments()
              
    
    def search_appointments(self):
        st.html("<H1 class='prompt'>SEARCH APPOINTMENTS</H1>")
        mobile_number=st.text_input("Number",placeholder="Customers Mobile Number")
        search_button=st.button("Search",use_container_width=True,key='search_appointment_button')
        st.html("<H1 class='prompt'>OR</H1>")
        all_appointments=st.button("Get all appointments",use_container_width=True,key='search_all_appointments')
        if all_appointments:
            
            fetch_all_appointments="""SELECT 
                p.Fname, 
                p.Lname, 
                p.MobileNumber, 
                t.Username AS TherapistUsername, 
                c.appointment_date, 
                c.appointment_time, 
                c.status, 
                c.created_at, 
                c.updated_at 
                FROM 
                    appointments c 
                JOIN 
                    patients_registration p 
                ON 
                    c.patient_id = p.ID 
                JOIN 
                    therapists_registration t
                ON 
                    c.therapist_id = t.ID
                """
            cursor.execute(fetch_all_appointments)
            result=cursor.fetchall()
            if result:
                df=pd.DataFrame(result,columns=['First Name','Last Name','Mobile Number','Therapist Username','date','time','status','Booking time','Updation time'])
                st.table(df)
                db.commit()
            else:
                st.error("No appointments found")
                db.rollback()        
        
        if search_button:
            try:
                fetch_customers_id="SELECT ID from patients_registration WHERE MobileNumber=%s"
                cursor.execute(fetch_customers_id,(mobile_number,))
                customer_id=cursor.fetchone()
                if customer_id:
                    fetch_appointments="""SELECT 
                        p.Fname, 
                        p.Lname, 
                        p.MobileNumber, 
                        t.Username AS TherapistUsername,  -- Fetch therapist's username
                        c.appointment_date, 
                        c.appointment_time, 
                        c.status, 
                        c.created_at, 
                        c.updated_at 
                    FROM 
                        appointments c 
                    JOIN 
                        patients_registration p 
                    ON 
                        c.patient_id = p.ID 
                    JOIN 
                        therapists_registration t
                    ON 
                        c.therapist_id = t.ID  
                    WHERE 
                        c.patient_id = %s"""
                    
                    cursor.execute(fetch_appointments,(customer_id[0],))
                    result=cursor.fetchall()
                    if result:
                        df=pd.DataFrame(result,columns=['First Name','Last Name','Mobile Number','Therapist ID','date','time','status','Booking time','Updation time'])
                        st.table(df)
            except Exception as e:
                st.error(f"There was an error: {e}")
                return

class BookAppointment:
    def __init__(self):
        st.markdown(f"<H1 class='prompt'>WELCOME {session_username.upper()}</H1>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"<H1 class='prompt'>PLEASE FILL UP THE PATIENT'S MOBILE NUMBER</H1>", unsafe_allow_html=True)
        
        mobile_number = st.text_input("Mobile Number", placeholder="Patients Mobile Number")
        
        fetch_existing_patients = "SELECT ID, Fname, Lname FROM patients_registration WHERE MobileNumber=%s"
        cursor.execute(fetch_existing_patients, (mobile_number,))
        existing_patient = cursor.fetchone()
        
        if existing_patient:
            col1, col2 = st.columns(2)
            patient_id = existing_patient[0]
            FirstName = existing_patient[1]
            LastName = existing_patient[2]

            Fname = col1.text_input("First Name", value=FirstName, disabled=True)
            Lname = col2.text_input("Last Name", value=LastName, disabled=True)

            fetch_available_therapists = "SELECT Username FROM therapists_registration WHERE status='available'"
            cursor.execute(fetch_available_therapists)
            available_therapists = cursor.fetchall()
            
            if available_therapists:
                st.markdown("---")
                st.html("<H1 style='text-align: center;'>APPOINTMENT BOOKING</H1>")
                
                therapist_options = [therapist[0] for therapist in available_therapists]
                therapist = st.selectbox("Available Therapists", therapist_options)
                
                # Moving the payment method selection here
                payment_method = st.selectbox("Select Payment Method", ["Credit Card", "Debit Card", "UPI", "Cash"])
                
                appointment_date = st.date_input("Appointment Date", value=pd.to_datetime('today').date(), format='DD/MM/YYYY')

                book_time = st.time_input("Appointment Time")
                
                confirm_booking = st.button("Confirm Booking", use_container_width=True, key='confirmation_button')
                
                if confirm_booking:
                    self.bookAppointment(patient_id, therapist, appointment_date, book_time, payment_method)
        else:
            st.error("No patient found with the provided mobile number.")
        
    def bookAppointment(self, patient_id, therapist, appointment_date, book_time, payment_method):
        fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username = %s"
        cursor.execute(fetch_therapist_id, (therapist,)) 
        therapist_id = cursor.fetchone()[0]
        
        appointment_datetime = datetime.combine(appointment_date, book_time)
        start_time = appointment_datetime
        end_time = start_time + pd.Timedelta(hours=1)

        check_availability_query = """
        SELECT COUNT(*)
        FROM appointments 
        WHERE therapist_id = %s
        AND (
            (appointment_time BETWEEN %s AND %s)
            OR (DATE_ADD(appointment_time, INTERVAL 1 HOUR) BETWEEN %s AND %s)
        )
        AND status = 'booked'
        """
        cursor.execute(check_availability_query, (therapist_id, start_time, end_time, start_time, end_time))
        is_available = cursor.fetchone()[0] == 0

        if is_available:
            try:
                confirm_booking_query = """
                INSERT INTO appointments (patient_id, therapist_id, appointment_date, appointment_time, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(confirm_booking_query, (patient_id, therapist_id, appointment_date, appointment_datetime, pd.to_datetime('now')))
                result = cursor.rowcount
                if result:
                    st.success("Appointment Booked Successfully.")
                    db.commit()
                    progress = st.progress(0)
                    for i in range(100):
                        t.sleep(0.02)
                        progress.progress(i + 1)
                    self.generate_invoice(patient_id, therapist_id, appointment_date, appointment_datetime, payment_method)
                else:
                    st.error("An error occurred.")
                    db.rollback()
            except Exception as e:
                st.error(f"An error occurred: {e}")
                db.rollback()
        else:
            st.error("The selected therapist is not available for the selected time slot.")

    def generate_invoice(self, patient_id, therapist_id, appointment_date, appointment_datetime, payment_method):
        try:
            fetch_patient_details = "SELECT Fname, Lname, MobileNumber FROM patients_registration WHERE ID=%s"
            cursor.execute(fetch_patient_details, (patient_id,))
            patient_details = cursor.fetchone()

            fetch_therapist_details = "SELECT Fname, Lname FROM therapists_registration WHERE ID=%s"
            cursor.execute(fetch_therapist_details, (therapist_id,))
            therapist_details = cursor.fetchone()

            # Generating INVOICE
            pdf = FPDF()
            pdf.add_page()

            # Setting up the title with Helvetica font
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(200, 10, "INVOICE", new_x="LMARGIN", new_y="NEXT", align='C')

            # Adding patient details
            pdf.set_font("Helvetica", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Patient: {patient_details[0]} {patient_details[1]}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Mobile: {patient_details[2]}", new_x="LMARGIN", new_y="NEXT")

            # Adding therapist details
            pdf.ln(5)
            pdf.cell(200, 10, f"Therapist: {therapist_details[0]} {therapist_details[1]}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Appointment Date: {appointment_date.strftime('%d/%m/%y')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Appointment Time: {appointment_datetime.strftime('%H:%M')}", new_x="LMARGIN", new_y="NEXT")

            # Adding service charge
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(200, 10, "Service Charge: 1000", new_x="LMARGIN", new_y="NEXT")

            # Adding selected payment method
            pdf.ln(10)
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(200, 10, f"Payment Method: {payment_method}", new_x="LMARGIN", new_y="NEXT")

            # Output the PDF
            invoice_filename = f"Invoice_{patient_id}_{appointment_date.strftime('%d-%m-%y')}.pdf"
            pdf.output(invoice_filename)

            # Provide the link to download the PDF
            with open(invoice_filename, 'rb') as file:
                if st.download_button(
                    label='Download Invoice',
                    data=file,
                    file_name=invoice_filename,
                    mime='application/pdf'):
                    os.remove(invoice_filename)
                    st.success("Invoice downloaded successfully.")
                    st.rerun()
        except Exception as e:
            st.error(f"An error occurred while generating the invoice: {e}")



class UpdateAppointments:
    def __init__(self):
        st.markdown(f"<H1 class='prompt'>WELCOME {session_username.upper()}</H1>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"<H1 class='prompt'>PLEASE ENTER THE APPOINTMENT ID</H1>", unsafe_allow_html=True)

        if 'appointment_id' not in st.session_state:
            st.session_state.appointment_id = ''
        if 'appointment_details' not in st.session_state:
            st.session_state.appointment_details = None
        if 'payment_method' not in st.session_state:
            st.session_state.payment_method = "Credit Card"  # Default payment method

        appointment_id = st.text_input("ID", placeholder="Appointment ID", value=st.session_state.appointment_id)

        if not appointment_id or not appointment_id.isdigit():
            st.error("Please enter a valid appointment ID.")
            return
        else:
            st.session_state.appointment_id = appointment_id
            self.updateAppointment(appointment_id)

    def updateAppointment(self, appointment_id):
        fetch_appointment_query = """SELECT 
            p.Fname, 
            p.Lname, 
            p.MobileNumber, 
            t.Username AS TherapistUsername,  
            c.appointment_date, 
            c.appointment_time, 
            c.status, 
            c.created_at, 
            c.updated_at 
        FROM 
            appointments c 
        JOIN 
            patients_registration p 
        ON 
            c.patient_id = p.ID 
        JOIN 
            therapists_registration t
        ON 
            c.therapist_id = t.ID  
        WHERE 
            c.ID = %s; """

        cursor.execute(fetch_appointment_query, (appointment_id,))
        result = cursor.fetchone()
        
        if result:
            st.session_state.appointment_details = result
            df = pd.DataFrame([result], columns=['First Name', 'Last Name', 'Mobile Number', 'Therapist Username', 'Appointment Date', 'Appointment Time', 'Status', 'Booking time', 'Update time'])
            st.table(df)

            col1, col2 = st.columns(2, gap='medium', vertical_alignment='center')
            first_name = col1.text_input("First Name", placeholder="First Name of the Patient", disabled=True, value=st.session_state.appointment_details[0], key='first_name')
            last_name = col2.text_input("Last Name", placeholder="Last Name of the Patient", disabled=True, value=st.session_state.appointment_details[1], key='last_name')
            number = st.text_input("Number", placeholder="Number of the Patient", value=st.session_state.appointment_details[2], key='patient_number')
            therapist = st.selectbox("Therapist", options=[st.session_state.appointment_details[3]], disabled=True, key='therapist')
            appointment_date = st.date_input("Appointment Date", value=pd.to_datetime(st.session_state.appointment_details[4]).date(), format='DD/MM/YYYY', key='appointment_date')
            appointment_time = st.time_input("Appointment Time", value=pd.to_datetime(st.session_state.appointment_details[5]).time(), key='appointment_time')
            status = st.selectbox("Status", options=['booked', 'cancelled', 'completed'], index=['booked', 'cancelled', 'completed'].index(st.session_state.appointment_details[6]), key='status')

            # Check if the appointment is completed
            is_completed = status == 'completed'

            if is_completed:
                # If the appointment is completed, only allow phone number update
                number = st.text_input("Number", placeholder="Number of the Patient", value=st.session_state.appointment_details[2], key='completed_patient_number')
                st.warning("You can only update the phone number for completed appointments.")
            else:
                # Check if the new appointment date is valid for rescheduling
                if appointment_date <= pd.to_datetime('today').date() and status == 'booked':
                    st.error("You can only reschedule appointments to a date greater than today or for cancelled appointments.")
                    return

            check_patient_query = """SELECT ID FROM patients_registration WHERE MobileNumber=%s"""
            cursor.execute(check_patient_query, (number,))
            patient_result = cursor.fetchone()

            if is_completed and not patient_result:
                st.error("The provided number does not exist in the patient database. Please enter a valid patient number.")
                return

            patient_id = patient_result[0] if patient_result else None

            if not is_completed:
                combined_datetime = datetime.combine(appointment_date, appointment_time)

                # Check therapist availability for the new time slot
                fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username = %s"
                cursor.execute(fetch_therapist_id, (therapist,))
                therapist_id = cursor.fetchone()[0]

                start_time = combined_datetime
                end_time = start_time + pd.Timedelta(hours=1)

                check_availability_query = """
                SELECT COUNT(*)
                FROM appointments 
                WHERE therapist_id = %s
                AND (
                    (appointment_time BETWEEN %s AND %s)
                    OR (DATE_ADD(appointment_time, INTERVAL 1 HOUR) BETWEEN %s AND %s)
                )
                AND status = 'booked'
                AND ID != %s  # Exclude the current appointment from the check
                """
                cursor.execute(check_availability_query, (therapist_id, start_time, end_time, start_time, end_time, appointment_id))
                is_available = cursor.fetchone()[0] == 0

                if not is_available:
                    st.error("The selected therapist is not available for the selected time slot.")
                    return

            update_button = st.button("Update Booking Details", use_container_width=True, key='update_booking_details')

            if update_button:
                try:
                    if is_completed:
                        # Only update the phone number for completed appointments
                        update_appointment_query = """UPDATE appointments SET 
                            patient_id=%s, 
                            updated_at=%s
                        WHERE ID=%s;"""
                        cursor.execute(update_appointment_query, (patient_id, pd.to_datetime('now'), appointment_id))
                    else:
                        update_appointment_query = """UPDATE appointments SET 
                            patient_id=%s, 
                            therapist_id=(SELECT ID FROM therapists_registration WHERE Username=%s),
                            appointment_date=%s,
                            appointment_time=%s,
                            status=%s,
                            updated_at=%s
                        WHERE ID=%s;"""
                        cursor.execute(update_appointment_query, (patient_id, therapist, appointment_date, combined_datetime, status, pd.to_datetime('now'), appointment_id))

                    result = cursor.rowcount

                    if result:
                        st.success("Appointment Updated Successfully.")
                        db.commit()
                        with st.spinner("Updating....Please Wait"):
                            t.sleep(2)

                        if not is_completed and status == 'booked':
                            # Only show payment options if the status is 'booked'
                            payment_method = st.selectbox("Select Payment Method", ["Credit Card", "Debit Card", "UPI", "Cash"], key='payment_method', index=["Credit Card", "Debit Card", "UPI", "Cash"].index(st.session_state.payment_method))

                            self.generate_invoice(patient_id, therapist_id, appointment_date, combined_datetime, payment_method)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    db.rollback()

        else:
            st.error("No appointment found with the provided ID.")

    def generate_invoice(self, patient_id, therapist_id, appointment_date, appointment_datetime, payment_method):
        try:
            fetch_patient_details = "SELECT Fname, Lname, MobileNumber FROM patients_registration WHERE ID=%s"
            cursor.execute(fetch_patient_details, (patient_id,))
            patient_details = cursor.fetchone()

            fetch_therapist_details = "SELECT Fname, Lname FROM therapists_registration WHERE ID=%s"
            cursor.execute(fetch_therapist_details, (therapist_id,))
            therapist_details = cursor.fetchone()

            # Generating INVOICE
            pdf = FPDF()
            pdf.add_page()

            # Setting up the title with Helvetica font
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(200, 10, "INVOICE", new_x="LMARGIN", new_y="NEXT", align='C')

            # Adding patient details
            pdf.set_font("Helvetica", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Patient: {patient_details[0]} {patient_details[1]}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Mobile: {patient_details[2]}", new_x="LMARGIN", new_y="NEXT")

            # Adding therapist details
            pdf.ln(5)
            pdf.cell(200, 10, f"Therapist: {therapist_details[0]} {therapist_details[1]}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Appointment Date: {appointment_date.strftime('%d/%m/%y')}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(200, 10, f"Appointment Time: {appointment_datetime.strftime('%H:%M')}", new_x="LMARGIN", new_y="NEXT")

            # Adding service charge
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(200, 10, "Service Charge: 1000", new_x="LMARGIN", new_y="NEXT")

            # Adding selected payment method
            pdf.ln(10)
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(200, 10, f"Payment Method: {payment_method}", new_x="LMARGIN", new_y="NEXT")

            # Output the PDF
            invoice_filename = f"Invoice_{patient_id}_{appointment_date.strftime('%d-%m-%y')}.pdf"
            pdf.output(invoice_filename)

            # Provide the link to download the PDF
            with open(invoice_filename, 'rb') as file:
                if st.download_button(
                    label='Download Invoice',
                    data=file,
                    file_name=invoice_filename,
                    mime='application/pdf'):
                    os.remove(invoice_filename)
                    st.success("Invoice downloaded successfully.")
                    st.rerun()
        except Exception as e:
            st.error(f"An error occurred while generating the invoice: {e}")

if __name__=="__main__":
    if Appointment_options=='View Appointments':
        view_appointments=ViewAppointments()
    if Appointment_options=='Book Appointment':
        book_appointment=BookAppointment()
    if Appointment_options=='Update Appointments':
        update_appointments=UpdateAppointments()