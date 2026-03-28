import streamlit as st
import pymysql
import pathlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Session state variables
session_username = st.session_state['username']
session_password = st.session_state['password']

# Database connection
db = pymysql.connect(host='localhost', user='root', password='', database='mhm')
cursor = db.cursor()

# Sidebar navigation
Sessions = st.sidebar.page_link("pages/therapists_sessions.py", label="Sessions", icon=":material/description:")
Progress = st.sidebar.page_link("pages/view_patients_progress.py", label="Patients Progress", icon=":material/acute:")
Chatbot = st.sidebar.page_link("pages/therapists_chatbot.py", label="Therapist Assistant AI", icon=":material/robot_2:")
if st.sidebar.button(label="Logout", use_container_width=True, key="back_to"):
    st.switch_page("Login_screen.py")

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("assets/style.css")
if css_path.exists():
    load_css(css_path)

class PatientSessionTracker:
    def __init__(self):
        self.therapist_id = self.get_therapist_id()
        st.html(f"<H1 class='prompt'>PATIENT SESSION NOTES TRACKER - {str.upper(session_username)}</H1>")
        
        # Main navigation
        view_options = st.selectbox(
            'Select View Option',
            options=[
                "Overview Dashboard",
                "Individual Patient Progress",
                "Session Details",
                "Comparative Analysis"
            ]
        )
        
        if view_options == "Overview Dashboard":
            self.overview_dashboard()
        elif view_options == "Individual Patient Progress":
            self.individual_patient_progress()
        elif view_options == "Session Details":
            self.session_details()
        elif view_options == "Comparative Analysis":
            self.comparative_analysis()

    def get_therapist_id(self):
        try:
            fetch_therapist_id = "SELECT ID FROM therapists_registration WHERE Username=%s"
            cursor.execute(fetch_therapist_id, (session_username,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            st.error(f"Error fetching therapist ID: {e}")
            return None

    def get_all_patient_sessions(self):
        """Fetch all patient session notes with patient details"""
        try:
            query = """
            SELECT 
                posn.*,
                CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name,
                pr.Email as patient_email
            FROM patients_own_session_notes posn
            JOIN patients_registration pr ON posn.patient_id = pr.ID
            ORDER BY posn.session_date DESC, posn.session_time DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            if results:
                columns = [
                    'ID', 'patient_id', 'session_date', 'session_notes', 'created_at', 
                    'updated_at', 'status', 'session_time', 'mood_rating', 'anxiety_level',
                    'depression_level', 'stress_level', 'sleep_quality', 'energy_level',
                    'social_interaction', 'self_care', 'primary_goal_progress', 
                    'secondary_goal_progress', 'exercise_days_week', 'panic_attacks_count',
                    'patient_name', 'patient_email'
                ]
                df = pd.DataFrame(results, columns=columns)
                df['session_date'] = pd.to_datetime(df['session_date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching patient sessions: {e}")
            return pd.DataFrame()

    def get_patient_sessions(self, patient_id):
        """Fetch sessions for a specific patient"""
        try:
            query = """
            SELECT 
                posn.*,
                CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name,
                pr.Email as patient_email
            FROM patients_own_session_notes posn
            JOIN patients_registration pr ON posn.patient_id = pr.ID
            WHERE posn.patient_id = %s
            ORDER BY posn.session_date DESC, posn.session_time DESC
            """
            cursor.execute(query, (patient_id,))
            results = cursor.fetchall()
            
            if results:
                columns = [
                    'ID', 'patient_id', 'session_date', 'session_notes', 'created_at', 
                    'updated_at', 'status', 'session_time', 'mood_rating', 'anxiety_level',
                    'depression_level', 'stress_level', 'sleep_quality', 'energy_level',
                    'social_interaction', 'self_care', 'primary_goal_progress', 
                    'secondary_goal_progress', 'exercise_days_week', 'panic_attacks_count',
                    'patient_name', 'patient_email'
                ]
                df = pd.DataFrame(results, columns=columns)
                df['session_date'] = pd.to_datetime(df['session_date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error fetching patient sessions: {e}")
            return pd.DataFrame()

    def overview_dashboard(self):
        """Display overview dashboard with key metrics and trends"""
        st.subheader("📊 Overview Dashboard")
        
        df = self.get_all_patient_sessions()
        if df.empty:
            st.info("No patient session notes available.")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", len(df))
        with col2:
            unique_patients = df['patient_id'].nunique()
            st.metric("Active Patients", unique_patients)
        with col3:
            recent_sessions = len(df[df['session_date'] >= (datetime.now() - timedelta(days=7))])
            st.metric("Sessions This Week", recent_sessions)
        with col4:
            avg_mood = df['mood_rating'].mean() if df['mood_rating'].notna().any() else 0
            st.metric("Avg Mood Rating", f"{avg_mood:.1f}")
        
        # Trends over time
        st.subheader("📈 Trends Over Time")
        
        # Group by date for trend analysis
        daily_metrics = df.groupby('session_date').agg({
            'mood_rating': 'mean',
            'anxiety_level': 'mean',
            'depression_level': 'mean',
            'stress_level': 'mean',
            'sleep_quality': 'mean',
            'energy_level': 'mean'
        }).reset_index()
        
        if not daily_metrics.empty:
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=('Mood Rating', 'Anxiety Level', 'Depression Level', 
                               'Stress Level', 'Sleep Quality', 'Energy Level'),
                vertical_spacing=0.1
            )
            
            metrics = ['mood_rating', 'anxiety_level', 'depression_level', 
                      'stress_level', 'sleep_quality', 'energy_level']
            colors = ['blue', 'red', 'purple', 'orange', 'green', 'pink']
            
            for i, (metric, color) in enumerate(zip(metrics, colors)):
                row = i // 3 + 1
                col = i % 3 + 1
                
                fig.add_trace(
                    go.Scatter(
                        x=daily_metrics['session_date'],
                        y=daily_metrics[metric],
                        mode='lines+markers',
                        name=metric.replace('_', ' ').title(),
                        line=dict(color=color)
                    ),
                    row=row, col=col
                )
            
            fig.update_layout(height=600, showlegend=False, title_text="Mental Health Metrics Trends")
            st.plotly_chart(fig, use_container_width=True)
        
        # Patient status distribution
        st.subheader("📋 Session Status Distribution")
        status_counts = df['status'].value_counts()
        
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Session Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Recent sessions table
        st.subheader("📅 Recent Sessions")
        recent_df = df.head(10)[['patient_name', 'session_date', 'session_time', 'status', 
                                'mood_rating', 'anxiety_level', 'depression_level']]
        st.dataframe(recent_df, use_container_width=True)

    def individual_patient_progress(self):
        """Display individual patient progress tracking"""
        st.subheader("👤 Individual Patient Progress")
        
        # Get list of patients
        all_df = self.get_all_patient_sessions()
        if all_df.empty:
            st.info("No patient session notes available.")
            return
        
        patients = all_df[['patient_id', 'patient_name']].drop_duplicates()
        patient_options = {f"{row['patient_name']} (ID: {row['patient_id']})": row['patient_id'] 
                          for _, row in patients.iterrows()}
        
        selected_patient_display = st.selectbox("Select Patient", list(patient_options.keys()))
        selected_patient_id = patient_options[selected_patient_display]
        
        # Get patient data
        patient_df = self.get_patient_sessions(selected_patient_id)
        if patient_df.empty:
            st.info("No sessions found for this patient.")
            return
        
        patient_name = patient_df.iloc[0]['patient_name']
        st.write(f"**Patient:** {patient_name}")
        st.write(f"**Total Sessions:** {len(patient_df)}")
        
        # Patient metrics over time
        if len(patient_df) > 1:
            st.subheader("📊 Progress Over Time")
            
            # Sort by date for proper time series
            patient_df_sorted = patient_df.sort_values('session_date')
            
            # Mental health metrics chart
            fig = go.Figure()
            
            metrics = ['mood_rating', 'anxiety_level', 'depression_level', 'stress_level']
            colors = ['blue', 'red', 'purple', 'orange']
            
            for metric, color in zip(metrics, colors):
                if patient_df_sorted[metric].notna().any():
                    fig.add_trace(go.Scatter(
                        x=patient_df_sorted['session_date'],
                        y=patient_df_sorted[metric],
                        mode='lines+markers',
                        name=metric.replace('_', ' ').title(),
                        line=dict(color=color)
                    ))
            
            fig.update_layout(
                title="Mental Health Metrics Progress",
                xaxis_title="Date",
                yaxis_title="Rating",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Lifestyle metrics chart
            fig2 = go.Figure()
            
            lifestyle_metrics = ['sleep_quality', 'energy_level', 'social_interaction', 'self_care']
            lifestyle_colors = ['green', 'yellow', 'cyan', 'magenta']
            
            for metric, color in zip(lifestyle_metrics, lifestyle_colors):
                if patient_df_sorted[metric].notna().any():
                    fig2.add_trace(go.Scatter(
                        x=patient_df_sorted['session_date'],
                        y=patient_df_sorted[metric],
                        mode='lines+markers',
                        name=metric.replace('_', ' ').title(),
                        line=dict(color=color)
                    ))
            
            fig2.update_layout(
                title="Lifestyle Metrics Progress",
                xaxis_title="Date",
                yaxis_title="Rating",
                hovermode='x unified'
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Goal progress
            if patient_df_sorted[['primary_goal_progress', 'secondary_goal_progress']].notna().any().any():
                st.subheader("🎯 Goal Progress")
                
                fig3 = go.Figure()
                
                if patient_df_sorted['primary_goal_progress'].notna().any():
                    fig3.add_trace(go.Scatter(
                        x=patient_df_sorted['session_date'],
                        y=patient_df_sorted['primary_goal_progress'],
                        mode='lines+markers',
                        name='Primary Goal',
                        line=dict(color='darkgreen')
                    ))
                
                if patient_df_sorted['secondary_goal_progress'].notna().any():
                    fig3.add_trace(go.Scatter(
                        x=patient_df_sorted['session_date'],
                        y=patient_df_sorted['secondary_goal_progress'],
                        mode='lines+markers',
                        name='Secondary Goal',
                        line=dict(color='darkblue')
                    ))
                
                fig3.update_layout(
                    title="Goal Achievement Progress",
                    xaxis_title="Date",
                    yaxis_title="Progress Rating",
                    hovermode='x unified'
                )
                st.plotly_chart(fig3, use_container_width=True)
        
        # Session summary statistics
        st.subheader("📈 Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Mental Health Metrics (Average):**")
            mental_health_avg = patient_df[['mood_rating', 'anxiety_level', 'depression_level', 'stress_level']].mean()
            for metric, avg in mental_health_avg.items():
                if not pd.isna(avg):
                    st.write(f"- {metric.replace('_', ' ').title()}: {avg:.1f}")
        
        with col2:
            st.write("**Lifestyle Metrics (Average):**")
            lifestyle_avg = patient_df[['sleep_quality', 'energy_level', 'social_interaction', 'self_care']].mean()
            for metric, avg in lifestyle_avg.items():
                if not pd.isna(avg):
                    st.write(f"- {metric.replace('_', ' ').title()}: {avg:.1f}")
        
        # Recent sessions for this patient
        st.subheader("📋 Recent Sessions")
        recent_sessions = patient_df.head(5)[['session_date', 'session_time', 'status', 
                                             'mood_rating', 'anxiety_level', 'depression_level']]
        st.dataframe(recent_sessions, use_container_width=True)

    def session_details(self):
        """Display detailed session information"""
        st.subheader("📝 Session Details")
        
        # Option to view by session ID or browse all
        view_type = st.radio("View Type", ["Search by Session ID", "Browse All Sessions"])
        
        if view_type == "Search by Session ID":
            session_id = st.text_input("Enter Session ID", placeholder="e.g., 1")
            
            if session_id and session_id.isdigit():
                session_data = self.get_session_by_id(int(session_id))
                if session_data is not None:
                    self.display_session_details(session_data)
                else:
                    st.info("No session found with this ID.")
        
        else:  # Browse All Sessions
            all_sessions = self.get_all_patient_sessions()
            if all_sessions.empty:
                st.info("No sessions available.")
                return
            
            # Display sessions in a paginated format
            sessions_per_page = 10
            total_sessions = len(all_sessions)
            total_pages = (total_sessions - 1) // sessions_per_page + 1
            
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * sessions_per_page
            end_idx = start_idx + sessions_per_page
            
            page_sessions = all_sessions.iloc[start_idx:end_idx]
            
            st.write(f"Showing {start_idx + 1}-{min(end_idx, total_sessions)} of {total_sessions} sessions")
            
            # Display session summary
            for _, session in page_sessions.iterrows():
                with st.expander(f"Session {session['ID']} - {session['patient_name']} ({session['session_date'].strftime('%Y-%m-%d')})"):
                    self.display_session_details(session)

    def get_session_by_id(self, session_id):
        """Get session details by ID"""
        try:
            query = """
            SELECT 
                posn.*,
                CONCAT(pr.Fname, ' ', pr.Lname) AS patient_name,
                pr.Email as patient_email
            FROM patients_own_session_notes posn
            JOIN patients_registration pr ON posn.patient_id = pr.ID
            WHERE posn.ID = %s
            """
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [
                    'ID', 'patient_id', 'session_date', 'session_notes', 'created_at', 
                    'updated_at', 'status', 'session_time', 'mood_rating', 'anxiety_level',
                    'depression_level', 'stress_level', 'sleep_quality', 'energy_level',
                    'social_interaction', 'self_care', 'primary_goal_progress', 
                    'secondary_goal_progress', 'exercise_days_week', 'panic_attacks_count',
                    'patient_name', 'patient_email'
                ]
                return pd.Series(result, index=columns)
            return None
            
        except Exception as e:
            st.error(f"Error fetching session: {e}")
            return None

    def display_session_details(self, session):
        """Display detailed session information"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information:**")
            st.write(f"Patient: {session['patient_name']}")
            st.write(f"Date: {session['session_date']}")
            st.write(f"Time: {session['session_time']}")
            st.write(f"Status: {session['status']}")
            
            st.write("**Mental Health Ratings:**")
            st.write(f"Mood Rating: {session['mood_rating'] or 'Not recorded'}")
            st.write(f"Anxiety Level: {session['anxiety_level'] or 'Not recorded'}")
            st.write(f"Depression Level: {session['depression_level'] or 'Not recorded'}")
            st.write(f"Stress Level: {session['stress_level'] or 'Not recorded'}")
        
        with col2:
            st.write("**Lifestyle Factors:**")
            st.write(f"Sleep Quality: {session['sleep_quality'] or 'Not recorded'}")
            st.write(f"Energy Level: {session['energy_level'] or 'Not recorded'}")
            st.write(f"Social Interaction: {session['social_interaction'] or 'Not recorded'}")
            st.write(f"Self Care: {session['self_care'] or 'Not recorded'}")
            
            st.write("**Progress & Activities:**")
            st.write(f"Primary Goal Progress: {session['primary_goal_progress'] or 'Not recorded'}")
            st.write(f"Secondary Goal Progress: {session['secondary_goal_progress'] or 'Not recorded'}")
            st.write(f"Exercise Days/Week: {session['exercise_days_week'] or 'Not recorded'}")
            st.write(f"Panic Attacks Count: {session['panic_attacks_count'] or 0}")
        
        if session['session_notes']:
            st.write("**Session Notes:**")
            st.text_area("Notes", session['session_notes'], height=100, disabled=True, key=f"notes_{session['ID']}", label_visibility="hidden")

    def comparative_analysis(self):
        """Display comparative analysis across patients"""
        st.subheader("📊 Comparative Analysis")
        
        df = self.get_all_patient_sessions()
        if df.empty:
            st.info("No patient session notes available.")
            return
        
        # Average metrics by patient
        patient_metrics = df.groupby(['patient_id', 'patient_name']).agg({
            'mood_rating': 'mean',
            'anxiety_level': 'mean',
            'depression_level': 'mean',
            'stress_level': 'mean',
            'sleep_quality': 'mean',
            'energy_level': 'mean',
            'social_interaction': 'mean',
            'self_care': 'mean',
            'exercise_days_week': 'mean',
            'panic_attacks_count': 'mean',
            'ID': 'count'  # Session count
        }).reset_index()
        
        patient_metrics.rename(columns={'ID': 'session_count'}, inplace=True)
        
        # Mental health comparison
        st.subheader("🧠 Mental Health Metrics Comparison")
        
        fig = px.bar(
            patient_metrics,
            x='patient_name',
            y=['mood_rating', 'anxiety_level', 'depression_level', 'stress_level'],
            title="Average Mental Health Metrics by Patient",
            barmode='group'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Lifestyle metrics comparison
        st.subheader("🌱 Lifestyle Metrics Comparison")
        
        fig2 = px.bar(
            patient_metrics,
            x='patient_name',
            y=['sleep_quality', 'energy_level', 'social_interaction', 'self_care'],
            title="Average Lifestyle Metrics by Patient",
            barmode='group'
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Session activity comparison
        st.subheader("📈 Session Activity")
        
        fig3 = px.bar(
            patient_metrics,
            x='patient_name',
            y='session_count',
            title="Total Sessions by Patient",
            color='session_count',
            color_continuous_scale='Blues'
        )
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
        
        # Correlation analysis
        st.subheader("🔗 Metric Correlations")
        
        numeric_cols = ['mood_rating', 'anxiety_level', 'depression_level', 'stress_level', 
                       'sleep_quality', 'energy_level', 'social_interaction', 'self_care']
        
        correlation_data = df[numeric_cols].corr()
        
        fig4 = px.imshow(
            correlation_data,
            title="Correlation Matrix of Mental Health and Lifestyle Metrics",
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        st.plotly_chart(fig4, use_container_width=True)
        
        # Summary statistics table
        st.subheader("📋 Patient Summary Table")
        display_metrics = patient_metrics.round(2)
        st.dataframe(display_metrics, use_container_width=True)


if __name__ == "__main__":
    if 'username' in st.session_state and 'password' in st.session_state:
        tracker = PatientSessionTracker()
    else:
        st.error("Please login first.")
        st.switch_page("Login_screen.py")