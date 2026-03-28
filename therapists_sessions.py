import streamlit as st
import pymysql
import pathlib
from datetime import datetime, time

session_username = st.session_state['username']
session_password = st.session_state['password']

db = pymysql.connect(host='localhost', user='root', password='', database='mhm')
cursor = db.cursor()

Main_panel = st.sidebar.page_link("pages/therapist_panel.py", label="Main Panel", icon=":material/home:")
Track_patients_own_session=st.sidebar.page_link("pages/track_patients_own_session.py",icon=":material/digital_wellbeing:")
Progress=st.sidebar.page_link("pages/view_patients_progress.py",label="Patients Progress",icon=":material/acute:")
Chatbot=st.sidebar.page_link("pages/therapists_chatbot.py",label="Therapist Assistant AI",icon=":material/robot_2:")



def add_session():
    st.header(":orange[ADD SESSION]", anchor=False, divider='orange')
    
    with st.form(key='session_form'):
        # Basic Session Information
        st.subheader("📋 Basic Session Information")
        col1, col2 = st.columns(2)
        
        with col1:
            appointment_id = st.number_input("Appointment ID", min_value=1, step=1)
            session_date = st.date_input("Session Date")
        
        with col2:
            session_time = st.time_input("Session Time")
            status = st.selectbox("Session Status", 
                                options=['pending', 'completed', 'cancelled'], 
                                index=0)
        
        session_notes = st.text_area("Session Notes", height=100)
        
        # Mental Health Metrics
        st.subheader("🧠 Mental Health Assessment (Rate 1-10)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mood_rating = st.slider("Mood Rating", 1, 10, 5, help="1=Very Poor, 10=Excellent")
            anxiety_level = st.slider("Anxiety Level", 1, 10, 5, help="1=No Anxiety, 10=Severe Anxiety")
            depression_level = st.slider("Depression Level", 1, 10, 5, help="1=No Depression, 10=Severe Depression")
        
        with col2:
            stress_level = st.slider("Stress Level", 1, 10, 5, help="1=No Stress, 10=Very Stressed")
            sleep_quality = st.slider("Sleep Quality", 1, 10, 5, help="1=Very Poor, 10=Excellent")
            energy_level = st.slider("Energy Level", 1, 10, 5, help="1=Very Low, 10=Very High")
        
        with col3:
            social_interaction = st.slider("Social Interaction", 1, 10, 5, help="1=Very Poor, 10=Excellent")
            self_care = st.slider("Self Care", 1, 10, 5, help="1=Very Poor, 10=Excellent")
            session_helpfulness = st.slider("Session Helpfulness", 1, 5, 3, help="1=Not Helpful, 5=Very Helpful")
        
        # Progress Tracking
        st.subheader("📈 Progress Tracking")
        col1, col2 = st.columns(2)
        
        with col1:
            primary_goal_progress = st.slider("Primary Goal Progress (%)", 0, 100, 50, help="0=No Progress, 100=Goal Achieved")
            secondary_goal_progress = st.slider("Secondary Goal Progress (%)", 0, 100, 50, help="0=No Progress, 100=Goal Achieved")
        
        with col2:
            homework_completion = st.selectbox("Homework Completion", 
                                             options=['not_assigned', 'not_completed', 'partially_completed', 'completed'],
                                             index=0)
            exercise_days_week = st.number_input("Exercise Days per Week", min_value=0, max_value=7, value=0)
        
        # Additional Metrics
        st.subheader("📊 Additional Health Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            panic_attacks_count = st.number_input("Panic Attacks Count (this period)", min_value=0, value=0)
            medication_compliance = st.selectbox("Medication Compliance", 
                                               options=[None, 'poor', 'fair', 'good', 'excellent'],
                                               index=0,
                                               format_func=lambda x: "Not Applicable" if x is None else x.title())
        
        # Professional Notes
        st.subheader("📝 Professional Documentation")
        col1, col2 = st.columns(2)
        
        with col1:
            progress_notes = st.text_area("Progress Notes", height=100, 
                                        help="Document patient's progress and improvements")
        
        with col2:
            therapist_observations = st.text_area("Therapist Observations", height=100,
                                                help="Professional observations and insights")
        
        submit_button = st.form_submit_button("Submit Session", type="primary")
        
        if submit_button:
            try:
                # DEBUG: Check constraint information (Fixed for older MySQL versions)
                st.info("🔍 Debugging constraint issue...")
                
                # Check constraint information - Fixed for older MySQL versions
                try:
                    # Try the modern approach first
                    check_constraints_query = """
                    SELECT CONSTRAINT_NAME, CHECK_CLAUSE 
                    FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS 
                    WHERE CONSTRAINT_SCHEMA = DATABASE()
                    AND CONSTRAINT_NAME LIKE '%sessions%'
                    """
                    cursor.execute(check_constraints_query)
                    constraint_info = cursor.fetchall()
                    
                    if constraint_info:
                        st.info("📋 Found constraints:")
                        for constraint_name, constraint_clause in constraint_info:
                            st.code(f"{constraint_name}: {constraint_clause}")
                    else:
                        st.info("📋 No check constraints found or not supported in this MySQL version")
                        
                except Exception as constraint_error:
                    st.warning(f"⚠️ Could not fetch constraint information: {constraint_error}")
                    st.info("💡 This is normal for older MySQL versions. Continuing with session creation...")
                
                # Check if the appointment ID exists and get full details
                # FIXED: Changed 'patients' to 'patients_registration'
                check_appointment_query = """
                SELECT a.ID, a.patient_id, a.therapist_id, 
                       CONCAT(p.Fname, ' ', p.Lname) as patient_name 
                FROM appointments a
                LEFT JOIN patients_registration p ON a.patient_id = p.ID
                WHERE a.ID = %s
                """
                cursor.execute(check_appointment_query, (appointment_id,))
                appointment_details = cursor.fetchone()
                
                if appointment_details is None:
                    st.error("❌ The appointment ID does not exist.")
                    return
                
                app_id, patient_id, appointment_therapist_id, patient_name = appointment_details
                st.success(f"✅ Found appointment {app_id} for patient: {patient_name} (ID: {patient_id})")
                
                # Check if there's a therapist mismatch
                fetch_therapist_query = "SELECT ID FROM therapists_registration WHERE Username=%s"
                cursor.execute(fetch_therapist_query, (session_username,))
                therapist_result = cursor.fetchone()
                
                if therapist_result is None:
                    st.error("❌ Therapist ID not found. Please check your username.")
                    return
                
                session_therapist_id = therapist_result[0]
                
                # Check for potential therapist mismatch
                if appointment_therapist_id and appointment_therapist_id != session_therapist_id:
                    st.warning(f"⚠️ Warning: Appointment therapist ID ({appointment_therapist_id}) differs from session therapist ID ({session_therapist_id})")
                    
                    # This might be the constraint violation - check if constraint enforces therapist match
                    st.error("❌ Potential constraint violation: Therapist mismatch between appointment and session")
                    st.info("💡 Solution: Either update the appointment to match current therapist, or use the correct therapist account")
                    return
                
                # Check if there are any existing sessions for the same therapist on the same day and time
                check_existing_sessions_query = """
                SELECT COUNT(*) FROM sessions 
                WHERE therapist_id=%s 
                AND session_date=%s 
                AND session_time=%s
                AND status != 'cancelled'
                """
                cursor.execute(check_existing_sessions_query, (session_therapist_id, session_date, session_time))
                existing_sessions_count = cursor.fetchone()[0]
                
                if existing_sessions_count > 0:
                    st.error("❌ A session is already scheduled for this therapist at the same date and time.")
                    return
                
                # Check for existing pending sessions for the same patient
                check_pending_sessions_query = """
                SELECT COUNT(*) FROM sessions 
                WHERE appointment_id IN (SELECT ID FROM appointments WHERE patient_id=%s) 
                AND status = 'pending'
                """
                cursor.execute(check_pending_sessions_query, (patient_id,))
                existing_pending_sessions = cursor.fetchone()[0]
                
                if existing_pending_sessions > 0 and status == 'pending':
                    st.error("❌ This patient already has a pending session. Please complete or cancel the existing session first.")
                    return
                
                # Check if the session date is in the past (only for pending sessions)
                if status == 'pending' and (session_date < datetime.today().date() or 
                   (session_date == datetime.today().date() and session_time < datetime.now().time())):
                    st.error("❌ Pending sessions cannot be scheduled in the past.")
                    return
                
                # Prepare medication compliance value (handle None)
                med_compliance = medication_compliance if medication_compliance else None
                
                # Comprehensive validation
                validation_errors = []
                
                # Validate rating fields
                rating_fields = {
                    'Mood Rating': mood_rating,
                    'Anxiety Level': anxiety_level,
                    'Depression Level': depression_level,
                    'Stress Level': stress_level,
                    'Sleep Quality': sleep_quality,
                    'Energy Level': energy_level,
                    'Social Interaction': social_interaction,
                    'Self Care': self_care,
                    'Session Helpfulness': session_helpfulness
                }
                
                for field_name, value in rating_fields.items():
                    if field_name == 'Session Helpfulness':
                        if value < 1 or value > 5:
                            validation_errors.append(f"{field_name} must be between 1 and 5 (current: {value})")
                    else:
                        if value < 1 or value > 10:
                            validation_errors.append(f"{field_name} must be between 1 and 10 (current: {value})")
                
                # Validate progress fields (should be 0-100)
                progress_fields = {
                    'Primary Goal Progress': primary_goal_progress,
                    'Secondary Goal Progress': secondary_goal_progress
                }
                
                for field_name, value in progress_fields.items():
                    if value < 0 or value > 100:
                        validation_errors.append(f"{field_name} must be between 0 and 100 (current: {value})")
                
                # Validate exercise days (should be 0-7)
                if exercise_days_week < 0 or exercise_days_week > 7:
                    validation_errors.append(f"Exercise days per week must be between 0 and 7 (current: {exercise_days_week})")
                
                # Validate panic attacks count (should be non-negative)
                if panic_attacks_count < 0:
                    validation_errors.append(f"Panic attacks count cannot be negative (current: {panic_attacks_count})")
                
                # Validate enum values
                valid_statuses = ['pending', 'completed', 'cancelled']
                if status not in valid_statuses:
                    validation_errors.append(f"Status must be one of: {valid_statuses} (current: {status})")
                
                valid_homework = ['not_assigned', 'not_completed', 'partially_completed', 'completed']
                if homework_completion not in valid_homework:
                    validation_errors.append(f"Homework completion must be one of: {valid_homework} (current: {homework_completion})")
                
                if med_compliance and med_compliance not in ['poor', 'fair', 'good', 'excellent']:
                    validation_errors.append(f"Medication compliance must be one of: ['poor', 'fair', 'good', 'excellent'] (current: {med_compliance})")
                
                # If there are validation errors, display them and return
                if validation_errors:
                    st.error("❌ Validation errors found:")
                    for error in validation_errors:
                        st.error(f"• {error}")
                    return
                
                # DEBUG: Show the values that will be inserted
                st.info("📋 Values to be inserted:")
                debug_values = {
                    "appointment_id": appointment_id,
                    "therapist_id": session_therapist_id,
                    "session_date": str(session_date),
                    "session_time": str(session_time),
                    "status": status,
                    "mood_rating": mood_rating,
                    "anxiety_level": anxiety_level,
                    "depression_level": depression_level,
                    "stress_level": stress_level,
                    "sleep_quality": sleep_quality,
                    "energy_level": energy_level,
                    "social_interaction": social_interaction,
                    "self_care": self_care,
                    "primary_goal_progress": primary_goal_progress,
                    "secondary_goal_progress": secondary_goal_progress,
                    "session_helpfulness": session_helpfulness,
                    "homework_completion": homework_completion,
                    "exercise_days_week": exercise_days_week,
                    "panic_attacks_count": panic_attacks_count,
                    "medication_compliance": med_compliance
                }
                st.json(debug_values)
                
                # Insert session into the database with all fields
                insert_session_query = """INSERT INTO sessions (
                    appointment_id, therapist_id, session_date, session_time, session_notes, 
                    status, mood_rating, anxiety_level, depression_level, stress_level, 
                    sleep_quality, energy_level, social_interaction, self_care, 
                    primary_goal_progress, secondary_goal_progress, session_helpfulness,
                    homework_completion, exercise_days_week, panic_attacks_count, 
                    medication_compliance, progress_notes, therapist_observations,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"""
                
                cursor.execute(insert_session_query, (
                    appointment_id, session_therapist_id, session_date, session_time, session_notes,
                    status, mood_rating, anxiety_level, depression_level, stress_level,
                    sleep_quality, energy_level, social_interaction, self_care,
                    primary_goal_progress, secondary_goal_progress, session_helpfulness,
                    homework_completion, exercise_days_week, panic_attacks_count,
                    med_compliance, progress_notes, therapist_observations
                ))
                
                db.commit()
                st.success("✅ Session added successfully with comprehensive health metrics!")
                
                # Display summary
                with st.expander("📋 Session Summary"):
                    st.write(f"**Appointment ID:** {appointment_id}")
                    st.write(f"**Patient:** {patient_name}")
                    st.write(f"**Session Date:** {session_date}")
                    st.write(f"**Session Time:** {session_time}")
                    st.write(f"**Status:** {status.title()}")
                    avg_mental_health = (mood_rating + (11 - anxiety_level) + (11 - depression_level) + 
                                       (11 - stress_level) + sleep_quality + energy_level + 
                                       social_interaction + self_care) / 8
                    st.write(f"**Average Mental Health Score:** {avg_mental_health:.1f}/10")
                    st.write(f"**Primary Goal Progress:** {primary_goal_progress}%")
                    st.write(f"**Secondary Goal Progress:** {secondary_goal_progress}%")
                    st.write(f"**Session Helpfulness:** {session_helpfulness}/5")
                
            except Exception as e:
                st.error(f"❌ An error occurred while adding the session: {e}")
                st.error(f"❌ Error details: {str(e)}")
                
                # Enhanced debugging for constraint violations
                if "Check constraint" in str(e) or "3819" in str(e) or "constraint" in str(e).lower():
                    st.error("🔍 This appears to be a check constraint violation.")
                    st.info("💡 Common causes:")
                    st.info("• Therapist mismatch between appointment and session")
                    st.info("• Date/time validation issues")
                    st.info("• Invalid enum values")
                    st.info("• Rating values outside 1-10 range")
                    st.info("• Cross-table validation failures")
                    
                    # Show the values that were being inserted for debugging
                    st.info("🔍 Debug values that were being inserted:")
                    debug_values = {
                        "appointment_id": appointment_id,
                        "session_date": str(session_date),
                        "session_time": str(session_time),
                        "status": status,
                        "mood_rating": mood_rating,
                        "anxiety_level": anxiety_level,
                        "depression_level": depression_level,
                        "stress_level": stress_level,
                        "sleep_quality": sleep_quality,
                        "energy_level": energy_level,
                        "social_interaction": social_interaction,
                        "self_care": self_care,
                        "primary_goal_progress": primary_goal_progress,
                        "secondary_goal_progress": secondary_goal_progress,
                        "session_helpfulness": session_helpfulness,
                        "homework_completion": homework_completion,
                        "exercise_days_week": exercise_days_week,
                        "panic_attacks_count": panic_attacks_count,
                        "medication_compliance": medication_compliance
                    }
                    st.json(debug_values)
                
                # Additional database-specific error handling
                elif "1054" in str(e):
                    st.error("🔍 Database column error - check if all required columns exist in the sessions table")
                elif "1062" in str(e):
                    st.error("🔍 Duplicate entry error - this session might already exist")
                elif "1452" in str(e):
                    st.error("🔍 Foreign key constraint error - check if appointment_id and therapist_id are valid")
                elif "1406" in str(e):
                    st.error("🔍 Data too long error - one of the text fields might exceed column limits")
                elif "1146" in str(e):
                    st.error("🔍 Table doesn't exist error - check if all referenced tables exist in the database")
                    st.info("💡 Make sure tables like 'sessions', 'appointments', 'patients_registration', and 'therapists_registration' exist")
                
                db.rollback()


def update_session():
    st.header(":orange[UPDATE SESSION]", anchor=False, divider='orange')
    
    # Fetch therapist ID based on the session username
    fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username=%s"
    cursor.execute(fetch_therapist_id, (session_username,))
    therapist_id_result = cursor.fetchone()
    
    if therapist_id_result is None:
        st.error("❌ Therapist ID not found. Please check your username.")
        return
    
    therapist_id = therapist_id_result[0]
    
    # Fetch sessions with patient information for better display
    fetch_sessions = """
    SELECT s.ID, s.appointment_id, s.session_date, s.session_time, 
           s.session_notes, s.status, s.mood_rating, s.anxiety_level, 
           s.depression_level, s.stress_level, s.sleep_quality, s.energy_level, 
           s.social_interaction, s.self_care, s.primary_goal_progress, 
           s.secondary_goal_progress, s.session_helpfulness, s.homework_completion, 
           s.exercise_days_week, s.panic_attacks_count, s.medication_compliance, 
           s.progress_notes, s.therapist_observations,
           CONCAT(p.Fname, ' ', p.Lname) as patient_name
    FROM sessions s
    LEFT JOIN appointments a ON s.appointment_id = a.ID
    LEFT JOIN patients_registration p ON a.patient_id = p.ID
    WHERE s.therapist_id = %s
    ORDER BY s.session_date DESC, s.session_time DESC
    """
    cursor.execute(fetch_sessions, (therapist_id,))
    sessions = cursor.fetchall()
    
    if not sessions:
        st.warning("⚠️ No sessions found to update.")
        return
    
    # Create simple session options display (ID only)
    session_options = []
    for session in sessions:
        session_id = session[0]
        display_text = f"{session_id}"
        session_options.append((session_id, display_text, session))
    
    # Display simple selectbox with session ID only
    selected_option = st.selectbox(
        "Select a session to update:",
        options=range(len(session_options)),
        format_func=lambda x: session_options[x][1]
    )
    
    # Get the selected session data
    selected_session_data = session_options[selected_option][2]
    
    # Unpack session data
    (session_id, appointment_id, current_date, current_time, current_notes, current_status,
     current_mood, current_anxiety, current_depression, current_stress, current_sleep,
     current_energy, current_social, current_self_care, current_primary_goal,
     current_secondary_goal, current_helpfulness, current_homework, current_exercise,
     current_panic_attacks, current_medication, current_progress_notes, 
     current_therapist_observations, patient_name) = selected_session_data
    
    # Handle time conversion (import datetime classes at the top)
    from datetime import datetime, time as time_class
    
    current_time_for_input = current_time
    if not isinstance(current_time, time_class):
        try:
            if hasattr(current_time, 'hour') and hasattr(current_time, 'minute'):
                current_time_for_input = time_class(current_time.hour, current_time.minute, 
                                                   getattr(current_time, 'second', 0))
            else:
                current_time_for_input = time_class(0, 0, 0)
        except:
            current_time_for_input = time_class(0, 0, 0)
    
    with st.form(key='update_session_form'):
        st.subheader(f"🔄 Updating Session for {patient_name}")
        
        # Display session info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Session ID:** {session_id}")
        with col2:
            st.info(f"**Appointment ID:** {appointment_id}")
        with col3:
            st.info(f"**Patient:** {patient_name}")
        
        # Basic Session Information
        st.subheader("📋 Basic Session Information")
        col1, col2 = st.columns(2)
        
        with col1:
            new_date = st.date_input("Session Date", value=current_date)
        
        with col2:
            new_time = st.time_input("Session Time", value=current_time_for_input)
            status_options = ['pending', 'completed', 'cancelled']
            status_index = status_options.index(current_status) if current_status in status_options else 0
            new_status = st.selectbox("Session Status", status_options, index=status_index)
        
        new_notes = st.text_area("Session Notes", value=current_notes or "", height=100)
        
        # Mental Health Metrics
        st.subheader("🧠 Mental Health Assessment (Rate 1-10)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_mood = st.slider("Mood Rating", 1, 10, current_mood or 5, help="1=Very Poor, 10=Excellent")
            new_anxiety = st.slider("Anxiety Level", 1, 10, current_anxiety or 5, help="1=No Anxiety, 10=Severe Anxiety")
            new_depression = st.slider("Depression Level", 1, 10, current_depression or 5, help="1=No Depression, 10=Severe Depression")
        
        with col2:
            new_stress = st.slider("Stress Level", 1, 10, current_stress or 5, help="1=No Stress, 10=Very Stressed")
            new_sleep = st.slider("Sleep Quality", 1, 10, current_sleep or 5, help="1=Very Poor, 10=Excellent")
            new_energy = st.slider("Energy Level", 1, 10, current_energy or 5, help="1=Very Low, 10=Very High")
        
        with col3:
            new_social = st.slider("Social Interaction", 1, 10, current_social or 5, help="1=Very Poor, 10=Excellent")
            new_self_care = st.slider("Self Care", 1, 10, current_self_care or 5, help="1=Very Poor, 10=Excellent")
            new_helpfulness = st.slider("Session Helpfulness", 1, 5, current_helpfulness or 3, help="1=Not Helpful, 5=Very Helpful")
        
        # Progress Tracking
        st.subheader("📈 Progress Tracking")
        col1, col2 = st.columns(2)
        
        with col1:
            new_primary_goal = st.slider("Primary Goal Progress (%)", 0, 100, current_primary_goal or 50, help="0=No Progress, 100=Goal Achieved")
            new_secondary_goal = st.slider("Secondary Goal Progress (%)", 0, 100, current_secondary_goal or 50, help="0=No Progress, 100=Goal Achieved")
        
        with col2:
            homework_options = ['not_assigned', 'not_completed', 'partially_completed', 'completed']
            homework_index = homework_options.index(current_homework) if current_homework in homework_options else 0
            new_homework = st.selectbox("Homework Completion", homework_options, index=homework_index)
            new_exercise = st.number_input("Exercise Days per Week", min_value=0, max_value=7, value=current_exercise or 0)
        
        # Additional Metrics
        st.subheader("📊 Additional Health Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            new_panic_attacks = st.number_input("Panic Attacks Count (this period)", min_value=0, value=current_panic_attacks or 0)
            
            # Handle medication compliance
            med_options = [None, 'poor', 'fair', 'good', 'excellent']
            med_index = 0
            if current_medication in med_options[1:]:
                med_index = med_options.index(current_medication)
            
            new_medication = st.selectbox("Medication Compliance", 
                                        options=med_options,
                                        index=med_index,
                                        format_func=lambda x: "Not Applicable" if x is None else x.title())
        
        # Professional Notes
        st.subheader("📝 Professional Documentation")
        col1, col2 = st.columns(2)
        
        with col1:
            new_progress_notes = st.text_area("Progress Notes", 
                                            value=current_progress_notes or "",
                                            height=100,
                                            help="Document patient's progress and improvements")
        
        with col2:
            new_therapist_observations = st.text_area("Therapist Observations", 
                                                    value=current_therapist_observations or "",
                                                    height=100,
                                                    help="Professional observations and insights")
        
        submit_button = st.form_submit_button("Update Session", type="primary")
        
        if submit_button:
            try:
                # Enhanced validation checks (datetime import moved to top)                
                # Validate status and timing
                current_datetime = datetime.now()
                session_datetime = datetime.combine(new_date, new_time)
                
                if new_status in ['completed', 'cancelled'] and session_datetime > current_datetime:
                    st.error("❌ Cannot mark future sessions as completed or cancelled.")
                    return
                
                if new_status == 'pending' and session_datetime < current_datetime:
                    st.error("❌ Cannot set pending sessions in the past.")
                    return
                
                # Check for scheduling conflicts (only if date or time changed)
                if new_date != current_date or new_time != current_time:
                    check_existing_sessions = """
                    SELECT COUNT(*) FROM sessions 
                    WHERE therapist_id=%s 
                    AND session_date=%s 
                    AND session_time=%s
                    AND ID != %s
                    AND status != 'cancelled'
                    """
                    cursor.execute(check_existing_sessions, (therapist_id, new_date, new_time, session_id))
                    existing_sessions_count = cursor.fetchone()[0]
                    
                    if existing_sessions_count > 0:
                        st.error("❌ A session is already scheduled for this therapist at the same date and time.")
                        return
                
                # Prepare medication compliance value
                med_compliance = new_medication if new_medication else None
                
                # Update session in the database
                update_query = """
                UPDATE sessions 
                SET session_date=%s, session_time=%s, session_notes=%s, status=%s,
                    mood_rating=%s, anxiety_level=%s, depression_level=%s, stress_level=%s,
                    sleep_quality=%s, energy_level=%s, social_interaction=%s, self_care=%s,
                    primary_goal_progress=%s, secondary_goal_progress=%s, session_helpfulness=%s,
                    homework_completion=%s, exercise_days_week=%s, panic_attacks_count=%s,
                    medication_compliance=%s, progress_notes=%s, therapist_observations=%s,
                    updated_at=NOW() 
                WHERE ID=%s
                """
                
                cursor.execute(update_query, (
                    new_date, new_time, new_notes, new_status,
                    new_mood, new_anxiety, new_depression, new_stress,
                    new_sleep, new_energy, new_social, new_self_care,
                    new_primary_goal, new_secondary_goal, new_helpfulness,
                    new_homework, new_exercise, new_panic_attacks,
                    med_compliance, new_progress_notes, new_therapist_observations,
                    session_id
                ))
                
                db.commit()
                st.success("✅ Session updated successfully with comprehensive health metrics!")
                
                # Display comprehensive update summary
                with st.expander("📋 Update Summary"):
                    st.write(f"**Session ID:** {session_id}")
                    st.write(f"**Patient:** {patient_name}")
                    st.write(f"**Updated Date:** {new_date}")
                    st.write(f"**Updated Time:** {new_time}")
                    st.write(f"**Status:** {current_status.title()} → {new_status.title()}")
                    
                    # Calculate mental health scores for comparison
                    if current_mood and current_anxiety and current_depression and current_stress:
                        avg_current = (current_mood + (11 - current_anxiety) + (11 - current_depression) + 
                                     (11 - current_stress) + current_sleep + current_energy + 
                                     current_social + current_self_care) / 8
                        avg_new = (new_mood + (11 - new_anxiety) + (11 - new_depression) + 
                                  (11 - new_stress) + new_sleep + new_energy + 
                                  new_social + new_self_care) / 8
                        score_change = avg_new - avg_current
                        
                        st.write(f"**Previous Mental Health Score:** {avg_current:.1f}/10")
                        st.write(f"**New Mental Health Score:** {avg_new:.1f}/10")
                        
                        if score_change > 0.5:
                            st.write(f"**Significant Improvement:** +{score_change:.1f} points 📈")
                        elif score_change > 0:
                            st.write(f"**Slight Improvement:** +{score_change:.1f} points ⬆️")
                        elif score_change < -0.5:
                            st.write(f"**Concerning Decline:** {score_change:.1f} points ⚠️")
                        elif score_change < 0:
                            st.write(f"**Slight Decline:** {score_change:.1f} points ⬇️")
                        else:
                            st.write("**No significant change in mental health score**")
                    
                    # Progress comparison
                    if current_primary_goal is not None:
                        primary_change = new_primary_goal - current_primary_goal
                        secondary_change = new_secondary_goal - current_secondary_goal
                        
                        st.write(f"**Primary Goal Progress:** {current_primary_goal}% → {new_primary_goal}% ({primary_change:+d}%)")
                        st.write(f"**Secondary Goal Progress:** {current_secondary_goal}% → {new_secondary_goal}% ({secondary_change:+d}%)")
                    
                    st.write(f"**Session Helpfulness:** {current_helpfulness or 'N/A'}/5 → {new_helpfulness}/5")
                
                # Auto-refresh to show updated data
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ An error occurred while updating the session: {e}")
                db.rollback()

if __name__ == "__main__":
    add_session()
    st.divider()
    update_session()