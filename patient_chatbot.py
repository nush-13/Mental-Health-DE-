import streamlit as st
import pymysql
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import time

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

# Chatbot responses and conversation patterns
GREETING_RESPONSES = [
    "Hello! 👋 I'm your mental wellness assistant. How can I help you today?",
    "Hi there! 😊 I'm here to help you explore your mental health data and provide support.",
    "Welcome! 🌟 I'm your personal wellness chatbot. What would you like to know about your progress?",
]

HELP_RESPONSES = [
    """I can help you with several things:
    
📊 **Data & Analytics:**
    • Show your mood trends over time
    • Display anxiety and stress patterns
    • Analyze your sleep quality
    • Track your exercise habits
    • View goal progress
    
💬 **General Support:**
    • Provide wellness tips
    • Offer motivational messages
    • Share coping strategies
    
Just ask me things like:
    • "Show me my mood trends"
    • "How has my anxiety been?"
    • "Display my sleep patterns"
    • "I need some motivation"
    """,
]

MOTIVATIONAL_RESPONSES = [
    "🌟 Remember, every day you track your mental health is a day you're investing in yourself!",
    "💪 You're stronger than you think! Your commitment to wellness shows your inner strength.",
    "🌈 Progress isn't always linear, and that's perfectly okay. You're doing amazing!",
    "✨ Small steps lead to big changes. Keep going, you've got this!",
    "🦋 Just like a butterfly, transformation takes time. Be patient with your journey.",
    "🌱 You're growing every day, even when you can't see it immediately.",
    "💖 Your mental health matters, and so do you. Thank you for prioritizing your wellbeing.",
]

WELLNESS_TIPS = [
    "💡 **Tip:** Try the 5-4-3-2-1 grounding technique when feeling anxious: 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.",
    "🧘 **Mindfulness:** Take 5 deep breaths right now. Inhale for 4 counts, hold for 4, exhale for 6.",
    "🚶 **Movement:** A 10-minute walk can boost your mood and energy levels significantly!",
    "😴 **Sleep:** Try to maintain a consistent sleep schedule. Your brain repairs itself during sleep!",
    "📝 **Journaling:** Writing down 3 things you're grateful for each day can improve your overall mood.",
    "🎵 **Music:** Listening to your favorite uplifting songs can instantly boost your mood!",
    "🌞 **Sunlight:** Spend a few minutes in natural sunlight each day - it helps regulate your mood and sleep.",
]

COPING_STRATEGIES = [
    """🛠️ **Quick Coping Strategies:**
    
    🔹 **For Anxiety:**
    • Box breathing (4-4-4-4 pattern)
    • Progressive muscle relaxation
    • Name 5 things you can see around you
    
    🔹 **For Low Mood:**
    • Do one small task you can complete
    • Listen to uplifting music
    • Reach out to a friend or family member
    
    🔹 **For Stress:**
    • Take a warm shower or bath
    • Practice gentle stretching
    • Use positive self-talk
    """,
    
    """🌿 **Long-term Wellness Strategies:**
    
    🔹 **Daily Habits:**
    • Maintain a regular sleep schedule
    • Eat nutritious meals regularly
    • Stay hydrated throughout the day
    
    🔹 **Weekly Goals:**
    • Exercise at least 3 times per week
    • Connect with friends or family
    • Engage in a hobby you enjoy
    
    🔹 **Monthly Check-ins:**
    • Review your progress and goals
    • Adjust your wellness routine as needed
    • Celebrate your achievements
    """,
]

# Custom CSS
st.markdown("""
<style>
    .chat-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #333;
        margin-left: 0;
        margin-right: auto;
        border-left: 4px solid #667eea;
    }
    
    .quick-actions {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.3rem 1rem;
        margin: 0.2rem;
        font-size: 0.8rem;
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

def get_session_data(patient_id, limit=30):
    """Get session data for analysis"""
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
        LIMIT %s
    """, (patient_id, limit))
    
    columns = ['session_date', 'mood_rating', 'anxiety_level', 'depression_level',
               'stress_level', 'sleep_quality', 'energy_level', 'social_interaction',
               'self_care', 'primary_goal_progress', 'secondary_goal_progress',
               'exercise_days_week', 'panic_attacks_count']
    
    data = cursor.fetchall()
    if data:
        return pd.DataFrame(data, columns=columns)
    return pd.DataFrame()

def create_mood_chart(df):
    """Create mood trends chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['session_date'],
        y=df['mood_rating'],
        mode='lines+markers',
        name='Mood Rating',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Date:</b> %{x}<br><b>Mood:</b> %{y}/10<extra></extra>'
    ))
    
    fig.update_layout(
        title="📈 Your Mood Trends Over Time",
        xaxis_title="Date",
        yaxis_title="Mood Rating (1-10)",
        template="plotly_white",
        height=400,
        showlegend=False
    )
    return fig

def create_anxiety_chart(df):
    """Create anxiety trends chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['session_date'],
        y=df['anxiety_level'],
        mode='lines+markers',
        name='Anxiety Level',
        line=dict(color='#f093fb', width=3),
        marker=dict(size=8),
        fill='tonexty',
        hovertemplate='<b>Date:</b> %{x}<br><b>Anxiety:</b> %{y}/10<extra></extra>'
    ))
    
    fig.update_layout(
        title="😰 Your Anxiety Levels Over Time",
        xaxis_title="Date",
        yaxis_title="Anxiety Level (1-10)",
        template="plotly_white",
        height=400,
        showlegend=False
    )
    return fig

def create_sleep_chart(df):
    """Create sleep quality chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['session_date'],
        y=df['sleep_quality'],
        name='Sleep Quality',
        marker_color='#a8edea',
        hovertemplate='<b>Date:</b> %{x}<br><b>Sleep Quality:</b> %{y}/10<extra></extra>'
    ))
    
    fig.update_layout(
        title="😴 Your Sleep Quality Patterns",
        xaxis_title="Date",
        yaxis_title="Sleep Quality (1-10)",
        template="plotly_white",
        height=400,
        showlegend=False
    )
    return fig

def create_comprehensive_chart(df):
    """Create comprehensive mental health chart"""
    fig = go.Figure()
    
    metrics = ['mood_rating', 'anxiety_level', 'depression_level', 'stress_level']
    colors = ['#667eea', '#f093fb', '#ffecd2', '#a8edea']
    names = ['Mood', 'Anxiety', 'Depression', 'Stress']
    
    for metric, color, name in zip(metrics, colors, names):
        fig.add_trace(go.Scatter(
            x=df['session_date'],
            y=df[metric],
            mode='lines+markers',
            name=name,
            line=dict(color=color, width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="🧠 Comprehensive Mental Health Overview",
        xaxis_title="Date",
        yaxis_title="Rating (1-10)",
        template="plotly_white",
        height=500,
        hovermode='x unified'
    )
    return fig

def create_exercise_chart(df):
    """Create exercise tracking chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['session_date'],
        y=df['exercise_days_week'],
        name='Exercise Days',
        marker_color='#90EE90',
        hovertemplate='<b>Date:</b> %{x}<br><b>Exercise Days:</b> %{y} days/week<extra></extra>'
    ))
    
    fig.update_layout(
        title="🏃‍♀️ Your Weekly Exercise Activity",
        xaxis_title="Date",
        yaxis_title="Days per Week",
        template="plotly_white",
        height=400,
        showlegend=False
    )
    return fig

def process_user_input(user_input, patient_id):
    """Process user input and return appropriate response"""
    user_input_lower = user_input.lower()
    
    # Greeting responses
    if any(greeting in user_input_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return random.choice(GREETING_RESPONSES), None, None
    
    # Help responses
    elif any(help_word in user_input_lower for help_word in ['help', 'what can you do', 'commands', 'options']):
        return random.choice(HELP_RESPONSES), None, None
    
    # Motivational responses
    elif any(word in user_input_lower for word in ['motivation', 'encourage', 'sad', 'down', 'depressed', 'low']):
        return random.choice(MOTIVATIONAL_RESPONSES), None, None
    
    # Wellness tips
    elif any(word in user_input_lower for word in ['tip', 'advice', 'help me', 'what should i do']):
        return random.choice(WELLNESS_TIPS), None, None
    
    # Coping strategies
    elif any(word in user_input_lower for word in ['cope', 'coping', 'strategy', 'anxious', 'stressed', 'panic']):
        return random.choice(COPING_STRATEGIES), None, None
    
    # Data visualization requests
    elif any(word in user_input_lower for word in ['mood', 'feeling']):
        df = get_session_data(patient_id)
        if not df.empty:
            fig = create_mood_chart(df)
            avg_mood = df['mood_rating'].mean()
            response = f"📊 Here's your mood trend analysis!\n\nYour average mood rating is {avg_mood:.1f}/10. "
            if avg_mood >= 7:
                response += "You've been maintaining a positive mood - that's wonderful! 🌟"
            elif avg_mood >= 5:
                response += "Your mood has been fairly stable. Keep focusing on what makes you feel good! 😊"
            else:
                response += "I notice your mood could use some attention. Remember, it's okay to have difficult days. Consider trying some mood-boosting activities! 💙"
            return response, fig, 'mood'
        else:
            return "I don't have enough mood data to show you yet. Start tracking your sessions to see your mood patterns! 📝", None, None
    
    elif any(word in user_input_lower for word in ['anxiety', 'anxious', 'worried', 'nervous']):
        df = get_session_data(patient_id)
        if not df.empty:
            fig = create_anxiety_chart(df)
            avg_anxiety = df['anxiety_level'].mean()
            response = f"📊 Here's your anxiety level analysis!\n\nYour average anxiety level is {avg_anxiety:.1f}/10. "
            if avg_anxiety <= 4:
                response += "Great job managing your anxiety! Your coping strategies seem to be working well. 😌"
            elif avg_anxiety <= 6:
                response += "Your anxiety levels are moderate. Keep practicing your coping techniques! 🌊"
            else:
                response += "Your anxiety has been elevated. Remember to use your breathing exercises and don't hesitate to reach out for support. 💙"
            return response, fig, 'anxiety'
        else:
            return "I don't have enough anxiety data to analyze yet. Keep tracking to see your patterns! 📝", None, None
    
    elif any(word in user_input_lower for word in ['sleep', 'sleeping', 'rest', 'tired']):
        df = get_session_data(patient_id)
        if not df.empty:
            fig = create_sleep_chart(df)
            avg_sleep = df['sleep_quality'].mean()
            response = f"📊 Here's your sleep quality analysis!\n\nYour average sleep quality is {avg_sleep:.1f}/10. "
            if avg_sleep >= 7:
                response += "Excellent sleep quality! Good sleep is fundamental to mental health. 😴✨"
            elif avg_sleep >= 5:
                response += "Your sleep quality is decent, but there's room for improvement. Try establishing a consistent bedtime routine! 🌙"
            else:
                response += "Your sleep quality needs attention. Poor sleep can significantly impact your mental health. Consider discussing sleep strategies with your therapist! 😴"
            return response, fig, 'sleep'
        else:
            return "I don't have enough sleep data to analyze yet. Start tracking to see your sleep patterns! 📝", None, None
    
    elif any(word in user_input_lower for word in ['exercise', 'workout', 'activity', 'physical']):
        df = get_session_data(patient_id)
        if not df.empty:
            fig = create_exercise_chart(df)
            avg_exercise = df['exercise_days_week'].mean()
            response = f"📊 Here's your exercise activity analysis!\n\nYou exercise an average of {avg_exercise:.1f} days per week. "
            if avg_exercise >= 4:
                response += "You're staying very active! Regular exercise is fantastic for mental health. 🏃‍♀️💪"
            elif avg_exercise >= 2:
                response += "You're moderately active. Try to increase your activity gradually for even better mental health benefits! 🚶‍♀️"
            else:
                response += "Try to incorporate more physical activity into your routine. Even small amounts can boost your mood significantly! 🌟"
            return response, fig, 'exercise'
        else:
            return "I don't have enough exercise data to analyze yet. Start tracking to see your activity patterns! 📝", None, None
    
    elif any(word in user_input_lower for word in ['overview', 'summary', 'all data', 'everything', 'comprehensive']):
        df = get_session_data(patient_id)
        if not df.empty:
            fig = create_comprehensive_chart(df)
            response = "📊 Here's your comprehensive mental health overview! This chart shows your mood, anxiety, depression, and stress levels over time. Look for patterns and trends that might help you understand your mental health journey better."
            return response, fig, 'comprehensive'
        else:
            return "I don't have enough data for a comprehensive overview yet. Keep tracking your sessions! 📝", None, None
    
    # Default response
    else:
        return "I'm not sure how to help with that specific request. Try asking me about your mood, anxiety, sleep patterns, or exercise habits. You can also ask for motivation, tips, or coping strategies! 🤖💙", None, None

def main():
    # Header
    st.markdown("""
        <div class="chat-header">
            <h1>🤖 Your Personal Wellness Assistant</h1>
            <p>I'm here to help you explore your mental health data and provide support!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get patient ID
    patient_id = get_patient_id(session_username)
    
    if not patient_id:
        st.error("Patient not found. Please check your login credentials.")
        return
    
    # Initialize chatbot session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        welcome_msg = random.choice(GREETING_RESPONSES)
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg, "chart": None, "chart_type": None})
    
    # Quick action buttons
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    st.markdown("**🚀 Quick Actions:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📈 Show Mood Trends"):
            user_input = "show me my mood trends"
            response, chart, chart_type = process_user_input(user_input, patient_id)
            st.session_state.chat_messages.append({"role": "user", "content": user_input, "chart": None, "chart_type": None})
            st.session_state.chat_messages.append({"role": "assistant", "content": response, "chart": chart, "chart_type": chart_type})
    
    with col2:
        if st.button("😰 Anxiety Analysis"):
            user_input = "show me my anxiety levels"
            response, chart, chart_type = process_user_input(user_input, patient_id)
            st.session_state.chat_messages.append({"role": "user", "content": user_input, "chart": None, "chart_type": None})
            st.session_state.chat_messages.append({"role": "assistant", "content": response, "chart": chart, "chart_type": chart_type})
    
    with col3:
        if st.button("😴 Sleep Patterns"):
            user_input = "show me my sleep patterns"
            response, chart, chart_type = process_user_input(user_input, patient_id)
            st.session_state.chat_messages.append({"role": "user", "content": user_input, "chart": None, "chart_type": None})
            st.session_state.chat_messages.append({"role": "assistant", "content": response, "chart": chart, "chart_type": chart_type})
    
    with col4:
        if st.button("💪 Get Motivation"):
            user_input = "I need some motivation"
            response, chart, chart_type = process_user_input(user_input, patient_id)
            st.session_state.chat_messages.append({"role": "user", "content": user_input, "chart": None, "chart_type": None})
            st.session_state.chat_messages.append({"role": "assistant", "content": response, "chart": chart, "chart_type": chart_type})
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for idx, message in enumerate(st.session_state.chat_messages):
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>🤖 Assistant:</strong><br>{message["content"]}
                    </div>
                """, unsafe_allow_html=True)
                
                # Display chart if available
                if message["chart"] is not None:
                    chart_key = f"chart_{message['chart_type']}_{idx}_{len(st.session_state.chat_messages)}"
                    st.plotly_chart(message["chart"], use_container_width=True, key=chart_key)
    
    # Chat input
    user_input = st.chat_input("Ask me about your mental health data, or request tips and motivation...")
    
    if user_input:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input, "chart": None, "chart_type": None})
        
        # Process input and get response
        with st.spinner("Thinking..."):
            time.sleep(0.5)  # Add slight delay for better UX
            response, chart, chart_type = process_user_input(user_input, patient_id)
        
        # Add assistant response
        st.session_state.chat_messages.append({"role": "assistant", "content": response, "chart": chart, "chart_type": chart_type})
        
        # Rerun to display new messages
        st.rerun()
    
    # Sidebar with helpful information
    st.sidebar.markdown("### 🤖 Chat Commands")
    st.sidebar.info("""
    **Try asking me:**
    • "Show my mood trends"
    • "How has my anxiety been?"
    • "Display my sleep patterns"
    • "Show my exercise activity"
    • "Give me a comprehensive overview"
    • "I need motivation"
    • "Give me some wellness tips"
    • "Help me cope with stress"
    """)
    
    st.sidebar.markdown("### 💡 Tips")
    st.sidebar.success("""
    • I can analyze your session data and create visual charts
    • Ask for motivation when you're feeling down
    • Request coping strategies when you're stressed
    • I'm here 24/7 to support your wellness journey!
    """)
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        welcome_msg = random.choice(GREETING_RESPONSES)
        st.session_state.chat_messages.append({"role": "assistant", "content": welcome_msg, "chart": None, "chart_type": None})
        st.rerun()
    if st.sidebar.button("🔙 Go Back"):
        st.switch_page("pages/patient_panel.py")
if __name__ == "__main__":
    main()