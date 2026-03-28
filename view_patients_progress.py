import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pymysql
import time


session_username = st.session_state['username']
session_password = st.session_state['password']

db=pymysql.connect(host='localhost',user='root',password='',database='mhm')
cursor=db.cursor()

Main_panel = st.sidebar.page_link("pages/therapist_panel.py", label="Main Panel", icon=":material/home:")
Sessions=st.sidebar.page_link("pages/therapists_sessions.py",label="Sessions",icon=":material/description:")
Chatbot=st.sidebar.page_link("pages/therapists_chatbot.py",label="Therapist Assistant AI",icon=":material/robot_2:")



def view_patient_progress_dashboard():
    """View progress dashboard for patients"""
    st.header("📈 Patient Progress Dashboard", anchor=False, divider='blue')
    
    # Get therapist ID
    fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username=%s"
    cursor.execute(fetch_therapist_id, (session_username,))
    therapist_id_result = cursor.fetchone()
    
    if therapist_id_result is None:
        st.error("Therapist ID not found.")
        return
    
    therapist_id = therapist_id_result[0]
    
    try:
        # Get patients with session data
        patients_query = """
        SELECT DISTINCT 
            pr.ID, 
            CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name
        FROM patients_registration pr
        JOIN appointments a ON pr.ID = a.patient_id
        JOIN sessions s ON a.ID = s.appointment_id
        WHERE s.therapist_id = %s AND s.mood_rating IS NOT NULL
        ORDER BY patient_name
        """
        
        cursor.execute(patients_query, (therapist_id,))
        patients = cursor.fetchall()
        
        if not patients:
            st.info("No patients found with progress data.")
            return
        
        # Patient selection
        patient_options = {f"{patient[1]}": patient[0] for patient in patients}
        selected_patient_name = st.selectbox("Select Patient", list(patient_options.keys()))
        selected_patient_id = patient_options[selected_patient_name]
        
        # Fetch progress data for selected patient
        progress_query = """
        SELECT 
            s.session_date, s.mood_rating, s.anxiety_level, s.depression_level, 
            s.stress_level, s.sleep_quality, s.energy_level, s.social_interaction,
            s.self_care, s.primary_goal_progress, s.secondary_goal_progress,
            s.session_helpfulness, s.homework_completion, s.exercise_days_week,
            s.panic_attacks_count, s.medication_compliance, s.progress_notes,
            s.therapist_observations
        FROM sessions s
        JOIN appointments a ON s.appointment_id = a.ID
        WHERE a.patient_id = %s AND s.therapist_id = %s AND s.mood_rating IS NOT NULL
        ORDER BY s.session_date ASC
        """
        
        cursor.execute(progress_query, (selected_patient_id, therapist_id))
        progress_data = cursor.fetchall()
        
        if not progress_data:
            st.info(f"No progress data available for {selected_patient_name}.")
            return
        
        # Convert to DataFrame
        columns = [
            'session_date', 'mood_rating', 'anxiety_level', 'depression_level',
            'stress_level', 'sleep_quality', 'energy_level', 'social_interaction',
            'self_care', 'primary_goal_progress', 'secondary_goal_progress',
            'session_helpfulness', 'homework_completion', 'exercise_days_week',
            'panic_attacks_count', 'medication_compliance', 'progress_notes',
            'therapist_observations'
        ]
        
        df = pd.DataFrame(progress_data, columns=columns)
        df['session_date'] = pd.to_datetime(df['session_date'])
        
        st.subheader(f"Progress Dashboard for {selected_patient_name}")
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["Mental Health Trends", "Goal Progress", "Behavioral Patterns", "Summary Stats"])
        
        with tab1:
            # Mental health metrics line chart
            fig_mental = go.Figure()
            
            mental_metrics = ['mood_rating', 'anxiety_level', 'depression_level', 'stress_level', 'sleep_quality']
            colors = ['#1f77b4', '#ff7f0e', '#d62728', '#9467bd', '#2ca02c']
            
            for metric, color in zip(mental_metrics, colors):
                fig_mental.add_trace(go.Scatter(
                    x=df['session_date'],
                    y=df[metric],
                    mode='lines+markers',
                    name=metric.replace('_', ' ').title(),
                    line=dict(color=color, width=2),
                    marker=dict(size=8)
                ))
            
            fig_mental.update_layout(
                title="Mental Health Metrics Over Time (1-10 Scale)",
                xaxis_title="Session Date",
                yaxis_title="Rating",
                yaxis=dict(range=[1, 10]),
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig_mental, use_container_width=True)
        
        with tab2:
            # Goal progress chart
            fig_goals = go.Figure()
            
            fig_goals.add_trace(go.Scatter(
                x=df['session_date'],
                y=df['primary_goal_progress'],
                mode='lines+markers',
                name='Primary Goal',
                line=dict(color='#2E8B57', width=3),
                marker=dict(size=10),
                fill='tonexty'
            ))
            
            fig_goals.add_trace(go.Scatter(
                x=df['session_date'],
                y=df['secondary_goal_progress'],
                mode='lines+markers',
                name='Secondary Goal',
                line=dict(color='#FF6347', width=3),
                marker=dict(size=10)
            ))
            
            fig_goals.update_layout(
                title="Goal Progress Over Time",
                xaxis_title="Session Date",
                yaxis_title="Progress (%)",
                yaxis=dict(range=[0, 100]),
                height=400
            )
            
            st.plotly_chart(fig_goals, use_container_width=True)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                # Exercise tracking
                fig_exercise = px.bar(
                    df, x='session_date', y='exercise_days_week',
                    title="Exercise Days Per Week",
                    color='exercise_days_week',
                    color_continuous_scale='Greens'
                )
                fig_exercise.update_layout(yaxis=dict(range=[0, 7]))
                st.plotly_chart(fig_exercise, use_container_width=True)
            
            with col2:
                # Session helpfulness
                fig_helpfulness = px.line(
                    df, x='session_date', y='session_helpfulness',
                    title="Session Helpfulness (1-5 Scale)",
                    markers=True
                )
                fig_helpfulness.update_layout(yaxis=dict(range=[1, 5]))
                st.plotly_chart(fig_helpfulness, use_container_width=True)
        
        with tab4:
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_mood = df['mood_rating'].mean()
                mood_trend = "📈" if df['mood_rating'].iloc[-1] > df['mood_rating'].iloc[0] else "📉"
                st.metric("Average Mood", f"{avg_mood:.1f}/10", delta=mood_trend)
            
            with col2:
                latest_primary_goal = df['primary_goal_progress'].iloc[-1]
                st.metric("Current Primary Goal", f"{latest_primary_goal}%")
            
            with col3:
                avg_exercise = df['exercise_days_week'].mean()
                st.metric("Avg Exercise Days", f"{avg_exercise:.1f}/week")
            
            with col4:
                avg_session_rating = df['session_helpfulness'].mean()
                st.metric("Avg Session Rating", f"{avg_session_rating:.1f}/5")
            
            # Additional insights
            st.subheader("📊 Progress Insights")
            
            # Recent progress notes
            if not df['progress_notes'].isna().all():
                recent_notes = df['progress_notes'].dropna().iloc[-3:]  # Last 3 notes
                st.write("**Recent Progress Notes:**")
                for i, note in enumerate(recent_notes, 1):
                    if note:
                        st.write(f"{i}. {note}")
            
            # Homework completion rate
            homework_completion_rate = (df['homework_completion'] == 'completed').mean() * 100
            st.write(f"**Homework Completion Rate:** {homework_completion_rate:.1f}%")
            
            # Medication compliance
            if not df['medication_compliance'].isna().all():
                compliance_counts = df['medication_compliance'].value_counts()
                st.write("**Medication Compliance Distribution:**")
                for compliance, count in compliance_counts.items():
                    st.write(f"- {compliance.title()}: {count} sessions")
                
    except Exception as e:
        st.error(f"Error displaying progress dashboard: {e}")

def main_progress_page():
    """Main function to handle progress tracking pages"""
    st.title("🧠 Mental Health Progress Tracking System")
    view_patient_progress_dashboard()

# Call this function in your main app
if __name__ == "__main__":
    main_progress_page()  