import streamlit as st
import pymysql
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, time
import random

# Database connection
@st.cache_resource
def init_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='mhm'
    )

db = init_connection()

# Get session credentials
session_username = st.session_state.get('username', 'Patient')
session_password = st.session_state.get('password', '')

# Positive motivational messages
POSITIVE_MESSAGES = [
    "🌟 Every small step forward is progress worth celebrating!",
    "💪 You're stronger than you know and braver than you feel.",
    "🌈 Today is a new opportunity to nurture your mental wellness.",
    "✨ Your journey to better mental health matters and so do you.",
    "🦋 Growth happens one day at a time. Be patient with yourself.",
    "🌸 You have the power to create positive change in your life.",
    "🌺 Remember: healing is not linear, and that's perfectly okay.",
    "🌞 Your mental health journey is unique and valuable.",
    "💖 Self-care isn't selfish—it's essential for your wellbeing.",
    "🌿 You're doing better than you think. Keep going!",
    "🎯 Focus on progress, not perfection.",
    "🌊 Like waves, difficult emotions will pass. You've got this!",
    "🦄 You are worthy of happiness, peace, and good mental health.",
    "🌟 Every day you choose to prioritize your mental health is a victory.",
    "🎈 Be gentle with yourself—you're doing the best you can."
]

# Custom CSS for appealing UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        color: #2c3e50 !important;
        font-weight: 500;
    }
    
    .positive-message {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        font-weight: 600;
        color: #333;
    }
    
    .section-header {
        background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 600;
        color: #333;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_patient_id(username):
    """Get patient ID from username"""
    cursor = db.cursor()
    cursor.execute("SELECT ID FROM patients_registration WHERE Username = %s", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_latest_session_data(patient_id):
    """Get latest session data for graphs"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT session_date, mood_rating, anxiety_level, depression_level, 
               stress_level, sleep_quality, energy_level, social_interaction, 
               self_care, primary_goal_progress, secondary_goal_progress,
               exercise_days_week, panic_attacks_count
        FROM sessions 
        WHERE appointment_id IN (
            SELECT id FROM appointments WHERE patient_id = %s
        )
        ORDER BY session_date DESC 
        LIMIT 10
    """, (patient_id,))
    
    columns = ['session_date', 'mood_rating', 'anxiety_level', 'depression_level',
               'stress_level', 'sleep_quality', 'energy_level', 'social_interaction',
               'self_care', 'primary_goal_progress', 'secondary_goal_progress',
               'exercise_days_week', 'panic_attacks_count']
    
    data = cursor.fetchall()
    if data:
        return pd.DataFrame(data, columns=columns)
    return pd.DataFrame()

def save_patient_session(patient_id, session_data):
    """Save patient's own session data"""
    cursor = db.cursor()
    
    insert_query = """
        INSERT INTO patients_own_session_notes 
        (patient_id, session_date, session_time, session_notes, mood_rating, 
         anxiety_level, depression_level, stress_level, sleep_quality, 
         energy_level, social_interaction, self_care, primary_goal_progress, 
         secondary_goal_progress, exercise_days_week, panic_attacks_count, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        patient_id, session_data['date'], session_data['time'], 
        session_data['notes'], session_data['mood'], session_data['anxiety'],
        session_data['depression'], session_data['stress'], session_data['sleep'],
        session_data['energy'], session_data['social'], session_data['self_care'],
        session_data['primary_goal'], session_data['secondary_goal'],
        session_data['exercise_days'], session_data['panic_attacks'], 'completed'
    ))
    db.commit()

# Main dashboard
def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🧠 Your Mental Wellness Dashboard</h1>
            <p>Welcome back! Track your progress and celebrate your journey.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display random positive message
    daily_message = random.choice(POSITIVE_MESSAGES)
    st.markdown(f"""
        <div class="positive-message">
            {daily_message}
        </div>
    """, unsafe_allow_html=True)
    
    # Get patient ID
    patient_id = get_patient_id(session_username)
    
    if not patient_id:
        st.error("Patient not found. Please check your login credentials.")
        return
    
    # Sidebar navigation
    st.sidebar.markdown("### 🌟 Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["📊 Dashboard Overview", "📈 Progress Tracking", "✍️ New Session Entry", "🎯 Goals & Insights","🤖 Your Consultant Chatbot"]
    )
    if st.sidebar.button("Logout",type='primary'):
        st.switch_page("Login_screen.py")
    
    
    if page == "📊 Dashboard Overview":
        dashboard_overview(patient_id)
    elif page == "📈 Progress Tracking":
        progress_tracking(patient_id)
    elif page == "✍️ New Session Entry":
        new_session_entry(patient_id)
    elif page == "🎯 Goals & Insights":
        goals_insights(patient_id)
    elif page == "🤖 Your Consultant Chatbot":
        st.switch_page("pages/patient_chatbot.py")

def dashboard_overview(patient_id):
    st.markdown('<div class="section-header">📊 Your Wellness Overview</div>', unsafe_allow_html=True)
    
    # Get latest session data
    df = get_latest_session_data(patient_id)
    
    if df.empty:
        st.info("No session data found. Start by adding your first session entry!")
        return
    
    # Display key metrics from latest session
    latest = df.iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="😊 Mood Rating",
            value=f"{latest['mood_rating']}/10",
            delta=None
        )
    
    with col2:
        st.metric(
            label="😰 Anxiety Level",
            value=f"{latest['anxiety_level']}/10",
            delta=None
        )
    
    with col3:
        st.metric(
            label="😴 Sleep Quality",
            value=f"{latest['sleep_quality']}/10",
            delta=None
        )
    
    with col4:
        st.metric(
            label="⚡ Energy Level",
            value=f"{latest['energy_level']}/10",
            delta=None
        )
    
    # Quick visualization
    st.markdown('<div class="section-header">📈 Recent Trends</div>', unsafe_allow_html=True)
    
    # Create a trend chart for mood over time
    if len(df) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['session_date'],
            y=df['mood_rating'],
            mode='lines+markers',
            name='Mood Rating',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Mood Rating Over Time",
            xaxis_title="Date",
            yaxis_title="Mood Rating (1-10)",
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def progress_tracking(patient_id):
    st.markdown('<div class="section-header">📈 Your Progress Journey</div>', unsafe_allow_html=True)
    
    df = get_latest_session_data(patient_id)
    
    if df.empty:
        st.info("No data available for progress tracking yet.")
        return
    
    # Mental health metrics comparison
    st.subheader("🧠 Mental Health Metrics")
    
    # Create subplot for mental health metrics
    fig = go.Figure()
    
    metrics = ['mood_rating', 'anxiety_level', 'depression_level', 'stress_level']
    colors = ['#667eea', '#f093fb', '#ffecd2', '#a8edea']
    metric_names = ['Mood', 'Anxiety', 'Depression', 'Stress']
    
    for i, (metric, color, name) in enumerate(zip(metrics, colors, metric_names)):
        fig.add_trace(go.Scatter(
            x=df['session_date'],
            y=df[metric],
            mode='lines+markers',
            name=name,
            line=dict(color=color, width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="Mental Health Metrics Trend",
        xaxis_title="Date",
        yaxis_title="Rating (1-10)",
        template="plotly_white",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Lifestyle metrics
    st.subheader("🏃‍♀️ Lifestyle & Wellness")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sleep quality and energy level
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['session_date'],
            y=df['sleep_quality'],
            mode='lines+markers',
            name='Sleep Quality',
            line=dict(color='#667eea', width=3)
        ))
        fig2.add_trace(go.Scatter(
            x=df['session_date'],
            y=df['energy_level'],
            mode='lines+markers',
            name='Energy Level',
            line=dict(color='#f093fb', width=3)
        ))
        
        fig2.update_layout(
            title="Sleep & Energy Trends",
            xaxis_title="Date",
            yaxis_title="Rating (1-10)",
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # Exercise and panic attacks
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df['session_date'],
            y=df['exercise_days_week'],
            name='Exercise Days/Week',
            marker_color='#a8edea'
        ))
        
        fig3.update_layout(
            title="Weekly Exercise Days",
            xaxis_title="Date",
            yaxis_title="Days per Week",
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig3, use_container_width=True)

def new_session_entry(patient_id):
    st.markdown('<div class="section-header">✍️ Record Your New Session</div>', unsafe_allow_html=True)
    
    st.write("Take a moment to reflect on your current state and record your session.")
    
    with st.form("new_session_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            session_date = st.date_input("📅 Session Date", value=date.today())
            session_time = st.time_input("🕐 Session Time", value=datetime.now().time())
            
            st.subheader("🧠 Mental Health Ratings")
            mood = st.slider("😊 How is your mood today?", 1, 10, 5, help="1=Very Low, 10=Excellent")
            anxiety = st.slider("😰 Anxiety Level", 1, 10, 5, help="1=No Anxiety, 10=Severe")
            depression = st.slider("😔 Depression Level", 1, 10, 5, help="1=Not Depressed, 10=Severely Depressed")
            stress = st.slider("😫 Stress Level", 1, 10, 5, help="1=No Stress, 10=Extremely Stressed")
            
        with col2:
            st.subheader("🌟 Wellness Metrics")
            sleep = st.slider("😴 Sleep Quality", 1, 10, 5, help="1=Very Poor, 10=Excellent")
            energy = st.slider("⚡ Energy Level", 1, 10, 5, help="1=Very Low, 10=Very High")
            social = st.slider("👥 Social Interaction", 1, 10, 5, help="1=Very Isolated, 10=Very Social")
            self_care = st.slider("💆‍♀️ Self-Care Level", 1, 10, 5, help="1=Poor, 10=Excellent")
            
            st.subheader("🎯 Goals & Activities")
            primary_goal = st.slider("🎯 Primary Goal Progress", 0, 100, 50, help="Percentage of completion")
            secondary_goal = st.slider("🎯 Secondary Goal Progress", 0, 100, 50, help="Percentage of completion")
            exercise_days = st.number_input("🏃‍♀️ Exercise Days This Week", 0, 7, 0)
            panic_attacks = st.number_input("😱 Panic Attacks Count", 0, 20, 0)
        
        st.subheader("📝 Session Notes")
        notes = st.text_area(
            "How are you feeling today? What's on your mind?",
            placeholder="Write about your thoughts, feelings, experiences, or anything you'd like to remember about today...",
            height=150
        )
        
        submitted = st.form_submit_button("💾 Save Session", use_container_width=True)
        
        if submitted:
            session_data = {
                'date': session_date,
                'time': session_time,
                'notes': notes,
                'mood': mood,
                'anxiety': anxiety,
                'depression': depression,
                'stress': stress,
                'sleep': sleep,
                'energy': energy,
                'social': social,
                'self_care': self_care,
                'primary_goal': primary_goal,
                'secondary_goal': secondary_goal,
                'exercise_days': exercise_days,
                'panic_attacks': panic_attacks
            }
            
            try:
                save_patient_session(patient_id, session_data)
                st.success("🎉 Session saved successfully! Great job on tracking your wellness.")
                st.balloons()
                
                # Show another positive message
                success_message = random.choice([
                    "🌟 You're doing amazing by staying consistent with your tracking!",
                    "💪 Every entry is a step forward in your wellness journey!",
                    "🎯 Your commitment to self-awareness is inspiring!",
                    "✨ Keep up the great work - you're making progress!"
                ])
                st.info(success_message)
                
            except Exception as e:
                st.error(f"An error occurred while saving your session: {str(e)}")

def goals_insights(patient_id):
    st.markdown('<div class="section-header">🎯 Goals & Personal Insights</div>', unsafe_allow_html=True)
    
    df = get_latest_session_data(patient_id)
    
    if df.empty:
        st.info("Add some session entries to see your personalized insights!")
        return
    
    # Goal progress visualization
    st.subheader("🎯 Goal Progress Tracking")
    
    latest = df.iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Primary goal progress
        fig_primary = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = latest['primary_goal_progress'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Primary Goal Progress"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "gray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}))
        
        fig_primary.update_layout(height=300)
        st.plotly_chart(fig_primary, use_container_width=True)
    
    with col2:
        # Secondary goal progress
        fig_secondary = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = latest['secondary_goal_progress'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Secondary Goal Progress"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#f093fb"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "gray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}))
        
        fig_secondary.update_layout(height=300)
        st.plotly_chart(fig_secondary, use_container_width=True)
    
    # Personal insights based on data
    st.subheader("💡 Your Personal Insights")
    
    # Calculate averages
    avg_mood = df['mood_rating'].mean()
    avg_anxiety = df['anxiety_level'].mean()
    avg_sleep = df['sleep_quality'].mean()
    avg_exercise = df['exercise_days_week'].mean()
    
    insights = []
    
    if avg_mood >= 7:
        insights.append("🌟 Your mood has been consistently positive! Keep up the great work.")
    elif avg_mood < 5:
        insights.append("💙 Your mood could use some attention. Consider reaching out to your therapist or trying mood-boosting activities.")
    
    if avg_anxiety >= 7:
        insights.append("🌊 Your anxiety levels have been high. Remember to practice your coping strategies and don't hesitate to seek support.")
    elif avg_anxiety <= 4:
        insights.append("😌 Great job managing your anxiety levels! Your coping strategies seem to be working well.")
    
    if avg_sleep >= 7:
        insights.append("😴 Excellent sleep quality! Good sleep is fundamental to mental health.")
    elif avg_sleep < 5:
        insights.append("🌙 Your sleep quality could be improved. Consider establishing a bedtime routine or discussing sleep strategies with your therapist.")
    
    if avg_exercise >= 4:
        insights.append("🏃‍♀️ You're staying active! Regular exercise is fantastic for mental health.")
    elif avg_exercise < 2:
        insights.append("🚶‍♀️ Try to incorporate more physical activity into your routine. Even small amounts can boost your mood!")
    
    if not insights:
        insights.append("📊 Keep tracking your progress - patterns will emerge as you add more data!")
    
    for insight in insights:
        st.markdown(f"""
            <div class="metric-card">
                {insight}
            </div>
        """, unsafe_allow_html=True)
    
    # Motivational section
    st.subheader("🌈 Keep Moving Forward")
    
    motivational_tips = [
        "🌱 Remember: Progress isn't always linear. Small steps count too!",
        "💪 You're stronger than your challenges. Every day you track is proof of your commitment.",
        "🌟 Celebrate small wins - they add up to big changes over time.",
        "🤗 Be patient and kind with yourself throughout this journey.",
        "📈 Look at your progress over weeks and months, not just day-to-day.",
    ]
    
    for tip in motivational_tips:
        st.markdown(f"""
            <div class="positive-message" style="margin: 0.5rem 0; padding: 0.5rem; font-size: 0.9rem;">
                {tip}
            </div>
        """, unsafe_allow_html=True)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 💖 Remember")
st.sidebar.info("You're doing great by taking care of your mental health. Every small step matters!")

# Run the main function
if __name__ == "__main__":
    main()