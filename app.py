import streamlit as st
import os
from dotenv import load_dotenv
from scheduling_agent import SchedulingAgent

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="AI Agents Scheduling System",
    page_icon="📅",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.session_state.agent = SchedulingAgent(api_key)
    else:
        st.session_state.agent = None

if 'goal_analyzed' not in st.session_state:
    st.session_state.goal_analyzed = False
    
if 'user_preferences_set' not in st.session_state:
    st.session_state.user_preferences_set = False
    
if 'schedule_generated' not in st.session_state:
    st.session_state.schedule_generated = False

# App title
st.title("AI Agents Scheduling System")
st.markdown("### Intelligent Preparation Assistant")

# Navigation
page = st.sidebar.radio("Navigation", ["Analyze Goal", "Set Preferences", "Generate Schedule", "View Schedule"])

# Analyze Goal Page
if page == "Analyze Goal":
    st.header("Analyze Your Preparation Goal")
    
    goal_description = st.text_area("What are you preparing for?", 
                                   placeholder="Example: I'm preparing for a job interview next week for a software developer position")
    
    if st.button("Analyze Goal"):
        if not goal_description:
            st.error("Please enter a goal description.")
        else:
            with st.spinner("Analyzing your goal..."):
                if st.session_state.agent:
                    result = st.session_state.agent.analyze_goal(goal_description)
                    st.session_state.goal_analyzed = True
                    
                    st.success("Goal analyzed successfully!")
                    st.subheader(result.get("goal_name", "Your Goal"))
                    
                    activities = result.get("preparation_activities", [])
                    if activities:
                        st.write("Preparation Activities:")
                        for activity in activities:
                            st.write(f"- **{activity.get('name')}**: {activity.get('estimated_hours')} hours ({activity.get('priority')} priority)")
                    
                    st.write(f"Total Preparation Time: {result.get('total_preparation_time', 'Unknown')}")
                    st.write(f"Recommended Timeline: {result.get('recommended_timeline', 'Unknown')}")
                else:
                    st.error("Missing OpenAI API Key. Please check your .env file.")

# Set Preferences Page
elif page == "Set Preferences":
    st.header("Set Your Preferences")
    
    name = st.text_input("Your Name")
    
    st.subheader("Time Constraints")
    col1, col2 = st.columns(2)
    with col1:
        wake_time = st.text_input("What time do you wake up?", "7:00 AM")
        productive_time = st.selectbox("When are you most productive?", 
                                       ["Morning", "Afternoon", "Evening", "Night"])
    with col2:
        sleep_time = st.text_input("What time do you go to sleep?", "11:00 PM")
        session_length = st.slider("Preferred session length (minutes)", 30, 120, 60)
    
    existing_commitments = st.text_area("Enter your existing commitments (one per line)", 
                                       placeholder="Example: Work 9 AM - 5 PM Monday-Friday\nGym 6 PM - 7 PM Tuesday, Thursday")
    
    if st.button("Save Preferences"):
        # Process commitments
        commitments = [commitment.strip() for commitment in existing_commitments.split("\n") if commitment.strip()]
        
        # Save to agent
        preferences = {
            "name": name,
            "time_constraints": {
                "wake_time": wake_time,
                "sleep_time": sleep_time
            },
            "productive_time": productive_time,
            "session_length_minutes": session_length,
            "commitments": commitments
        }
        
        if st.session_state.agent:
            st.session_state.agent.collect_user_preferences(preferences)
            st.session_state.user_preferences_set = True
            st.success("Preferences saved successfully!")
        else:
            st.error("Agent not initialized. Please check your API key.")

# Generate Schedule Page
elif page == "Generate Schedule":
    st.header("Generate Your Schedule")
    
    if not st.session_state.goal_analyzed:
        st.warning("Please analyze a goal first.")
        if st.button("Go to Goal Analysis"):
            st.session_state.page = "Analyze Goal"
    elif not st.session_state.user_preferences_set:
        st.warning("Please set your preferences first.")
        if st.button("Go to Preferences"):
            st.session_state.page = "Set Preferences"
    else:
        if st.session_state.agent and st.session_state.agent.preparation_context:
            goals = list(st.session_state.agent.preparation_context.keys())
            
            selected_goal = st.selectbox("Select a goal to schedule", goals)
            days = st.slider("Number of days to schedule", 1, 14, 7)
            
            if st.button("Generate Schedule"):
                with st.spinner("Generating your personalized schedule..."):
                    schedule = st.session_state.agent.generate_schedule(selected_goal, days)
                    st.session_state.schedule_generated = True
                    
                    st.success("Schedule generated successfully!")
                    st.write(f"Total scheduled hours: {schedule.get('total_scheduled_hours', 0)}")
                    
                    if "schedule_notes" in schedule:
                        st.info(schedule["schedule_notes"])
        else:
            st.error("No goals analyzed yet.")

# View Schedule Page
elif page == "View Schedule":
    st.header("Your Preparation Schedule")
    
    if not st.session_state.schedule_generated:
        st.warning("No schedule has been generated yet.")
        if st.button("Generate a Schedule"):
            st.session_state.page = "Generate Schedule"
    else:
        if st.session_state.agent and st.session_state.agent.schedule:
            for day in st.session_state.agent.schedule:
                date = day.get("date", "Unknown date")
                st.subheader(date)
                
                activities = day.get("activities", [])
                if activities:
                    for activity in activities:
                        start = activity.get("start_time", "")
                        end = activity.get("end_time", "")
                        name = activity.get("activity_name", "")
                        notes = activity.get("notes", "")
                        
                        st.write(f"**{start} - {end}**: {name}")
                        if notes:
                            st.write(f"*{notes}*")
                else:
                    st.write("No activities scheduled for this day.")
                
                st.markdown("---")
        else:
            st.error("No schedule available.")

# Run the app with: streamlit run app.py