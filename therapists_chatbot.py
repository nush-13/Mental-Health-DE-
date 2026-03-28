import streamlit as st
import pymysql
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class PatientMetrics:
    """Data class to hold patient metrics for analysis"""
    mood_rating: List[int]
    anxiety_level: List[int]
    depression_level: List[int]
    stress_level: List[int]
    sleep_quality: List[int]
    energy_level: List[int]
    social_interaction: List[int]
    self_care: List[int]
    session_dates: List[str]

class TherapistChatbot:
    def __init__(self, host='localhost', user='root', password='', database='mhm'):
        """Initialize the therapist chatbot with database connection"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    @st.cache_resource
    def get_connection(_self):
        """Get database connection with caching"""
        try:
            connection = pymysql.connect(
                host=_self.host,
                user=_self.user,
                password=_self.password,
                database=_self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                autocommit=True
            )
            return connection
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SQL query and return results"""
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            connection.ping(reconnect=True)
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            st.error(f"Query execution failed: {e}")
            return []
    
    def get_patient_list(self) -> List[Dict]:
        """Get list of all registered patients"""
        query = """
        SELECT ID, Fname, Lname, Gender, Email, Username
        FROM patients_registration
        ORDER BY Fname, Lname
        """
        return self.execute_query(query)
    
    def search_patients(self, search_term: str) -> List[Dict]:
        """Search patients by name, email, or username"""
        search_term = f"%{search_term}%"
        query = """
        SELECT ID, Fname, Lname, Gender, Email, Username, MobileNumber
        FROM patients_registration
        WHERE Fname LIKE %s 
           OR Lname LIKE %s 
           OR Email LIKE %s 
           OR Username LIKE %s
           OR CONCAT(Fname, ' ', Lname) LIKE %s
        ORDER BY Fname, Lname
        """
        return self.execute_query(query, (search_term, search_term, search_term, search_term, search_term))
    
    def get_patient_info(self, patient_id: int) -> Dict:
        """Get detailed patient information"""
        query = """
        SELECT pr.*, 
               COUNT(DISTINCT a.ID) as total_appointments,
               COUNT(DISTINCT s.ID) as therapist_sessions,
               COUNT(DISTINCT pos.ID) as patient_self_sessions
        FROM patients_registration pr
        LEFT JOIN appointments a ON pr.ID = a.patient_id
        LEFT JOIN sessions s ON a.ID = s.appointment_id
        LEFT JOIN patients_own_session_notes pos ON pr.ID = pos.patient_id
        WHERE pr.ID = %s
        GROUP BY pr.ID
        """
        results = self.execute_query(query, (patient_id,))
        return results[0] if results else {}
    
    def get_therapist_sessions(self, patient_id: int) -> List[Dict]:
        """Get all therapist-recorded sessions for a patient"""
        query = """
        SELECT s.*, a.appointment_date, a.appointment_time,
               pr.Fname, pr.Lname
        FROM sessions s
        JOIN appointments a ON s.appointment_id = a.ID
        JOIN patients_registration pr ON a.patient_id = pr.ID
        WHERE a.patient_id = %s
        ORDER BY s.session_date DESC
        """
        return self.execute_query(query, (patient_id,))
    
    def get_patient_self_sessions(self, patient_id: int) -> List[Dict]:
        """Get all patient self-recorded sessions"""
        query = """
        SELECT pos.*, pr.Fname, pr.Lname
        FROM patients_own_session_notes pos
        JOIN patients_registration pr ON pos.patient_id = pr.ID
        WHERE pos.patient_id = %s
        ORDER BY pos.session_date DESC
        """
        return self.execute_query(query, (patient_id,))
    
    def analyze_patient_progress(self, patient_id: int) -> Dict:
        """Comprehensive analysis of patient progress"""
        therapist_sessions = self.get_therapist_sessions(patient_id)
        patient_sessions = self.get_patient_self_sessions(patient_id)
        
        analysis = {
            'patient_id': patient_id,
            'therapist_sessions_count': len(therapist_sessions),
            'patient_sessions_count': len(patient_sessions),
            'therapist_metrics': self._analyze_session_metrics(therapist_sessions),
            'patient_metrics': self._analyze_session_metrics(patient_sessions),
            'progress_trends': self._calculate_progress_trends(therapist_sessions, patient_sessions),
            'recommendations': []
        }
        
        analysis['recommendations'] = self._generate_recommendations(analysis)
        return analysis
    
    def _analyze_session_metrics(self, sessions: List[Dict]) -> Dict:
        """Analyze metrics from session data"""
        if not sessions:
            return {}
        
        metrics = {
            'mood_rating': [],
            'anxiety_level': [],
            'depression_level': [],
            'stress_level': [],
            'sleep_quality': [],
            'energy_level': [],
            'social_interaction': [],
            'self_care': []
        }
        
        for session in sessions:
            for metric in metrics.keys():
                if session.get(metric) is not None:
                    metrics[metric].append(session[metric])
        
        stats = {}
        for metric, values in metrics.items():
            if values:
                stats[metric] = {
                    'current': values[0] if values else None,
                    'average': np.mean(values),
                    'trend': self._calculate_trend(values),
                    'improvement': values[0] - values[-1] if len(values) > 1 else 0,
                    'values': values,
                    'dates': [s['session_date'] for s in sessions if s.get(metric) is not None]
                }
        
        return stats
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a metric"""
        if len(values) < 2:
            return 'insufficient_data'
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_progress_trends(self, therapist_sessions: List[Dict], patient_sessions: List[Dict]) -> Dict:
        """Calculate overall progress trends"""
        trends = {}
        
        if therapist_sessions:
            primary_goals = [s['primary_goal_progress'] for s in therapist_sessions if s.get('primary_goal_progress')]
            secondary_goals = [s['secondary_goal_progress'] for s in therapist_sessions if s.get('secondary_goal_progress')]
            
            if primary_goals:
                trends['primary_goal_trend'] = self._calculate_trend(primary_goals)
                trends['primary_goal_current'] = primary_goals[0]
            
            if secondary_goals:
                trends['secondary_goal_trend'] = self._calculate_trend(secondary_goals)
                trends['secondary_goal_current'] = secondary_goals[0]
        
        return trends
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate treatment recommendations based on analysis"""
        recommendations = []
        
        therapist_metrics = analysis.get('therapist_metrics', {})
        patient_metrics = analysis.get('patient_metrics', {})
        
        for source, metrics in [('Therapist observations', therapist_metrics), ('Patient self-reports', patient_metrics)]:
            for metric, data in metrics.items():
                if isinstance(data, dict) and data.get('trend') == 'declining':
                    if metric in ['mood_rating', 'energy_level', 'sleep_quality']:
                        recommendations.append(f"⚠️ {source}: {metric.replace('_', ' ').title()} showing declining trend - consider intervention")
                    elif metric in ['anxiety_level', 'depression_level', 'stress_level']:
                        recommendations.append(f"⚠️ {source}: {metric.replace('_', ' ').title()} increasing - may need additional support")
        
        common_metrics = set(therapist_metrics.keys()) & set(patient_metrics.keys())
        for metric in common_metrics:
            if (isinstance(therapist_metrics[metric], dict) and 
                isinstance(patient_metrics[metric], dict)):
                
                therapist_avg = therapist_metrics[metric].get('average', 0)
                patient_avg = patient_metrics[metric].get('average', 0)
                
                if abs(therapist_avg - patient_avg) > 2:
                    recommendations.append(f"📊 Significant discrepancy in {metric.replace('_', ' ')} between therapist and patient reports")
        
        progress_trends = analysis.get('progress_trends', {})
        if progress_trends.get('primary_goal_trend') == 'declining':
            recommendations.append("🎯 Primary goal progress declining - reassess goals and treatment approach")
        
        if not recommendations:
            recommendations.append("✅ Patient showing stable progress - continue current treatment plan")
        
        return recommendations[:5]
    
    def get_recent_sessions(self, days: int = 7) -> List[Dict]:
        """Get recent sessions across all patients"""
        query = """
        SELECT s.*, a.appointment_date, pr.Fname, pr.Lname, 'therapist' as source
        FROM sessions s
        JOIN appointments a ON s.appointment_id = a.ID
        JOIN patients_registration pr ON a.patient_id = pr.ID
        WHERE s.session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        
        UNION ALL
        
        SELECT pos.ID, pos.patient_id, NULL as therapist_id, pos.session_date, pos.session_notes,
               pos.created_at, pos.updated_at, pos.status, pos.session_time, pos.mood_rating,
               pos.anxiety_level, pos.depression_level, pos.stress_level, pos.sleep_quality,
               pos.energy_level, pos.social_interaction, pos.self_care, pos.primary_goal_progress,
               pos.secondary_goal_progress, NULL as session_helpfulness, NULL as homework_completion,
               pos.exercise_days_week, pos.panic_attacks_count, NULL as medication_compliance,
               NULL as progress_notes, NULL as therapist_observations, pos.session_date as appointment_date,
               pr.Fname, pr.Lname, 'patient' as source
        FROM patients_own_session_notes pos
        JOIN patients_registration pr ON pos.patient_id = pr.ID
        WHERE pos.session_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        
        ORDER BY session_date DESC
        """
        return self.execute_query(query, (days, days))

# Initialize the chatbot
@st.cache_resource
def init_chatbot():
    return TherapistChatbot()

def main():
    st.set_page_config(
        page_title="Therapist Assistant Chatbot",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🧠 Therapist Assistant Chatbot")
    st.markdown("---")
    
    # Initialize chatbot
    bot = init_chatbot()
    
    # Test database connection
    connection = bot.get_connection()
    if not connection:
        st.error("❌ Cannot connect to database. Please check your connection settings.")
        st.info("💡 Make sure MySQL server is running and database 'mhm' exists.")
        return
    
    st.success("✅ Connected to database successfully!")
    
    # Sidebar for navigation
    st.sidebar.title("🔧 Controls")
    
    # Main functionality options
    option = st.sidebar.selectbox(
        "Choose an option:",
        ["🏠 Home", "👥 Patient List", "🔍 Search Patients", "👤 Patient Dashboard", "📅 Recent Sessions","🔙 Go Back"]
    )
    
    if option == "🏠 Home":
        st.markdown("""
        ## Welcome to the Therapist Assistant Chatbot! 👋
        
        This application helps therapists manage and analyze patient data efficiently.
        
        ### Features:
        - 👥 **Patient Management**: View all registered patients
        - 🔍 **Smart Search**: Find patients by name, email, or username
        - 👤 **Patient Dashboard**: Comprehensive patient analysis and progress tracking
        - 📅 **Recent Activity**: Monitor recent sessions across all patients
        - 📊 **Progress Analytics**: Visual charts and trend analysis
        - 💡 **AI Recommendations**: Automated treatment suggestions
        
        ### Quick Start:
        1. Use the sidebar to navigate between different features
        2. Start with "Patient List" to see all registered patients
        3. Use "Patient Dashboard" for detailed analysis of specific patients
        4. Check "Recent Sessions" for latest activity
        
        ---
        *Select an option from the sidebar to get started!*
        """)
    
    elif option == "👥 Patient List":
        st.header("👥 All Registered Patients")
        
        patients = bot.get_patient_list()
        if patients:
            df = pd.DataFrame(patients)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn("Patient ID", width="small"),
                    "Fname": st.column_config.TextColumn("First Name"),
                    "Lname": st.column_config.TextColumn("Last Name"),
                    "Gender": st.column_config.TextColumn("Gender", width="small"),
                    "Email": st.column_config.TextColumn("Email"),
                    "Username": st.column_config.TextColumn("Username")
                }
            )
            st.info(f"📊 Total patients: {len(patients)}")
        else:
            st.warning("No patients found in the database.")
    
    elif option == "🔍 Search Patients":
        st.header("🔍 Search Patients")
        
        search_term = st.text_input("Enter search term (name, email, or username):", placeholder="e.g., John, john@email.com")
        
        if search_term:
            with st.spinner("Searching..."):
                results = bot.search_patients(search_term)
            
            if results:
                st.success(f"Found {len(results)} patients:")
                df = pd.DataFrame(results)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn("Patient ID", width="small"),
                        "Fname": st.column_config.TextColumn("First Name"),
                        "Lname": st.column_config.TextColumn("Last Name"),
                        "Gender": st.column_config.TextColumn("Gender", width="small"),
                        "Email": st.column_config.TextColumn("Email"),
                        "Username": st.column_config.TextColumn("Username"),
                        "MobileNumber": st.column_config.NumberColumn("Mobile Number")
                    }
                )
            else:
                st.warning("No patients found matching your search criteria.")
    
    elif option == "👤 Patient Dashboard":
        st.header("👤 Patient Dashboard")
        
        # Patient selection
        patients = bot.get_patient_list()
        if not patients:
            st.warning("No patients found in the database.")
            return
        
        patient_options = {f"{p['Fname']} {p['Lname']} (ID: {p['ID']})": p['ID'] for p in patients}
        
        selected_patient = st.selectbox("Select a patient:", options=list(patient_options.keys()))
        
        if selected_patient:
            patient_id = patient_options[selected_patient]
            
            with st.spinner("Loading patient data..."):
                patient_info = bot.get_patient_info(patient_id)
                analysis = bot.analyze_patient_progress(patient_id)
            
            if patient_info:
                # Patient Info Cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Appointments", patient_info.get('total_appointments', 0))
                
                with col2:
                    st.metric("Therapist Sessions", patient_info.get('therapist_sessions', 0))
                
                with col3:
                    st.metric("Self Sessions", patient_info.get('patient_self_sessions', 0))
                
                with col4:
                    st.metric("Gender", patient_info.get('Gender', 'N/A'))
                
                st.markdown("---")
                
                # Patient Details
                with st.expander("📋 Patient Information", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Name:** {patient_info.get('Fname', '')} {patient_info.get('Lname', '')}")
                        st.write(f"**Email:** {patient_info.get('Email', 'N/A')}")
                    with col2:
                        st.write(f"**Username:** {patient_info.get('Username', 'N/A')}")
                        st.write(f"**Patient ID:** {patient_id}")
                
                # Progress Analysis
                if analysis['therapist_metrics'] or analysis['patient_metrics']:
                    st.markdown("### 📈 Progress Analysis")
                    
                    # Create tabs for different views
                    tab1, tab2, tab3 = st.tabs(["📊 Metrics Overview", "📈 Trend Charts", "💡 Recommendations"])
                    
                    with tab1:
                        # Therapist Metrics
                        if analysis['therapist_metrics']:
                            st.subheader("👨‍⚕️ Therapist Observations")
                            
                            metrics_data = []
                            for metric, data in analysis['therapist_metrics'].items():
                                if isinstance(data, dict):
                                    metrics_data.append({
                                        'Metric': metric.replace('_', ' ').title(),
                                        'Current': f"{data['current']:.1f}",
                                        'Average': f"{data['average']:.1f}"
                                    })
                            
                            if metrics_data:
                                st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
                        
                        # Patient Metrics
                        if analysis['patient_metrics']:
                            st.subheader("📱 Patient Self-Reports")
                            
                            metrics_data = []
                            for metric, data in analysis['patient_metrics'].items():
                                if isinstance(data, dict):
                                    trend_emoji = {'improving': '📈', 'declining': '📉', 'stable': '➡️'}.get(data['trend'], '❓')
                                    metrics_data.append({
                                        'Metric': metric.replace('_', ' ').title(),
                                        'Current': f"{data['current']:.1f}",
                                        'Average': f"{data['average']:.1f}",
                                        'Trend': f"{data['trend'].title()} {trend_emoji}"
                                    })
                            
                            if metrics_data:
                                st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
                    
                    with tab2:
                        # Trend Charts
                        st.subheader("📈 Progress Trends")
                        
                        # Combine therapist and patient metrics for comparison
                        all_metrics = set()
                        if analysis['therapist_metrics']:
                            all_metrics.update(analysis['therapist_metrics'].keys())
                        if analysis['patient_metrics']:
                            all_metrics.update(analysis['patient_metrics'].keys())
                        
                        if all_metrics:
                            selected_metric = st.selectbox("Select metric to visualize:", list(all_metrics))
                            
                            fig = go.Figure()
                            
                            # Add therapist data
                            if selected_metric in analysis.get('therapist_metrics', {}):
                                data = analysis['therapist_metrics'][selected_metric]
                                if 'values' in data and 'dates' in data:
                                    fig.add_trace(go.Scatter(
                                        x=data['dates'],
                                        y=data['values'],
                                        mode='lines+markers',
                                        name='Therapist Observations',
                                        line=dict(color='blue')
                                    ))
                            
                            # Add patient data
                            if selected_metric in analysis.get('patient_metrics', {}):
                                data = analysis['patient_metrics'][selected_metric]
                                if 'values' in data and 'dates' in data:
                                    fig.add_trace(go.Scatter(
                                        x=data['dates'],
                                        y=data['values'],
                                        mode='lines+markers',
                                        name='Patient Self-Reports',
                                        line=dict(color='red')
                                    ))
                            
                            fig.update_layout(
                                title=f'{selected_metric.replace("_", " ").title()} Progress Over Time',
                                xaxis_title='Date',
                                yaxis_title='Rating',
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No metric data available for visualization.")
                    
                    with tab3:
                        # Recommendations
                        st.subheader("💡 Treatment Recommendations")
                        
                        for i, rec in enumerate(analysis['recommendations'], 1):
                            if rec.startswith('✅'):
                                st.success(rec)
                            elif rec.startswith('⚠️'):
                                st.warning(rec)
                            elif rec.startswith('📊') or rec.startswith('🎯'):
                                st.info(rec)
                            else:
                                st.write(f"{i}. {rec}")
                
                else:
                    st.info("No session data available for this patient.")
            
            else:
                st.error(f"Patient with ID {patient_id} not found.")
    
    elif option == "📅 Recent Sessions":
        st.header("📅 Recent Sessions")
        
        days = st.slider("Select number of days:", min_value=1, max_value=30, value=7)
        
        with st.spinner("Loading recent sessions..."):
            sessions = bot.get_recent_sessions(days)
        
        if sessions:
            st.success(f"Found {len(sessions)} sessions in the last {days} days")
            
            # Convert to DataFrame for better display
            session_data = []
            for session in sessions:
                source_emoji = "👨‍⚕️" if session['source'] == 'therapist' else "📱"
                session_data.append({
                    'Source': f"{source_emoji} {session['source'].title()}",
                    'Patient': f"{session['Fname']} {session['Lname']}",
                    'Date': session['session_date'],
                    'Mood Rating': session.get('mood_rating', 'N/A'),
                    'Anxiety Level': session.get('anxiety_level', 'N/A'),
                    'Stress Level': session.get('stress_level', 'N/A')
                })
            
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Session statistics
            col1, col2, col3 = st.columns(3)
            
            therapist_sessions = len([s for s in sessions if s['source'] == 'therapist'])
            patient_sessions = len([s for s in sessions if s['source'] == 'patient'])
            
            with col1:
                st.metric("Therapist Sessions", therapist_sessions)
            with col2:
                st.metric("Patient Self-Sessions", patient_sessions)
            with col3:
                st.metric("Total Sessions", len(sessions))
        
        else:
            st.info(f"No sessions found in the last {days} days.")
    elif option=="🔙 Go Back":
        st.switch_page("pages/therapist_panel.py")

if __name__ == "__main__":
    main()