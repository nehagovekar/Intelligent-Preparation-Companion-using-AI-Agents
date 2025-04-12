import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from openai import OpenAI

class SchedulingAgent:
    """Main agent that coordinates preparation scheduling"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.user_profile = {}
        self.preparation_context = {}
        self.schedule = []
    
    def get_ai_response(self, prompt: str, system_message: str, temperature: float = 0.7) -> Dict:
        """Get a structured response from the OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            result = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"text": result}
                
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return {"error": str(e)}
    
    def analyze_goal(self, goal_description: str) -> Dict:
        """Analyze a preparation goal using the analysis agent"""
        
        prompt = f"""
        I need to prepare for: {goal_description}
        
        Please analyze this goal and help me understand:
        1. What specific preparation activities will I need to do?
        2. How much time should I allocate for each activity?
        3. What's a reasonable timeline for these preparations?
        4. How should I prioritize different parts of this preparation?
        """
        
        system_message = """
        You are an expert preparation analyst who helps people understand what they need to do to prepare
        effectively for goals. You break down preparation needs into concrete actionable steps with time estimates.
        
        Return your response as a valid JSON object with this structure:
        {
            "goal_name": "Short name for the goal",
            "preparation_activities": [
                {
                    "name": "Name of activity",
                    "description": "Description of what this activity involves",
                    "estimated_hours": 0,
                    "priority": "high/medium/low"
                }
            ],
            "total_preparation_time": "Estimated total hours needed",
            "recommended_timeline": "Recommended preparation timeline"
        }
        """
        
        result = self.get_ai_response(prompt, system_message)
        
        if "goal_name" in result:
            self.preparation_context[result["goal_name"]] = result
        
        return result
    
    def collect_user_preferences(self, user_data: Dict) -> None:
        """Collect user preferences for scheduling"""
        self.user_profile = user_data
    
    def generate_schedule(self, goal_name: str, days: int = 7) -> Dict:
        """Generate a schedule for a specific goal"""
        if goal_name not in self.preparation_context:
            return {"error": f"Goal '{goal_name}' not found. Please analyze this goal first."}
        
        goal_data = self.preparation_context[goal_name]
        
        prompt = f"""
        I need to create a schedule for preparing for: {goal_name}
        
        Total preparation time needed: {goal_data.get('total_preparation_time', '0')} hours
        
        Activities to schedule:
        {json.dumps(goal_data.get('preparation_activities', []), indent=2)}
        
        User profile and preferences:
        {json.dumps(self.user_profile, indent=2)}
        
        Please create an optimal daily schedule for the next {days} days that:
        1. Prioritizes high-priority activities
        2. Creates a realistic and sustainable preparation plan
        3. Includes appropriate breaks and prevents burnout
        """
        
        system_message = """
        You are an expert scheduling assistant who creates personalized preparation schedules.
        You understand how to create realistic schedules that set people up for success.
        
        Return your response as a valid JSON object with this structure:
        {
            "daily_schedules": [
                {
                    "date": "YYYY-MM-DD",
                    "activities": [
                        {
                            "activity_name": "Name of preparation activity",
                            "start_time": "HH:MM",
                            "end_time": "HH:MM",
                            "notes": "Any specific focus for this session"
                        }
                    ]
                }
            ],
            "total_scheduled_hours": 0,
            "schedule_notes": "Any notes about the overall schedule"
        }
        """
        
        schedule_result = self.get_ai_response(prompt, system_message)
        
        if "daily_schedules" in schedule_result:
            self.schedule = schedule_result["daily_schedules"]
        
        return schedule_result