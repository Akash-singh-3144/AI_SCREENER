import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return None
    return api_key

def analyze_resume(jd_text: str, resume_text: str, api_key: str) -> dict:
    """
    Compares the resume against the JD and returns a structured JSON response using Gemini.
    """
    genai.configure(api_key=api_key)
    
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        target_model = None
        # Look for standard models first
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']:
            if pref in models:
                target_model = pref
                break
                
        if target_model is None:
            if not models:
                raise ValueError("No generative models available for this API key.")
            target_model = models[0] # Pick the first available model that generates content
            
        model_name_clean = target_model.replace("models/", "")
    except Exception as e:
        return {"score": 0, "strengths": [f"API Error finding model: {e}"], "gaps": [], "recommendation": "Not Fit"}
        
    system_instruction = """
    You are an expert technical recruiter and AI Resume Screener.
    Your task is to evaluate a candidate's resume against a Job Description.
    You MUST respond with ONLY a valid JSON object. Do not include any markdown formatting like ```json.
    
    The JSON object must have EXACTLY these keys:
    - "score": integer between 0 and 100 representing the match percentage.
    - "strengths": list of 2 or 3 strings highlighting the candidate's key strengths for the role.
    - "gaps": list of 2 or 3 strings highlighting the candidate's key gaps or missing skills.
    - "recommendation": A string that MUST BE exactly one of: "Strong Fit", "Moderate Fit", or "Not Fit".
    """
    
    model = genai.GenerativeModel(
        model_name=model_name_clean,
        generation_config={"temperature": 0.2}
    )
    
    full_prompt = f"{system_instruction}\n\nJOB DESCRIPTION:\n{jd_text}\n\n====================\n\nCANDIDATE RESUME:\n{resume_text}"
    
    try:
        response = model.generate_content(full_prompt)
        
        result_content = response.text
        
        # Clean up potential markdown formatting
        result_content = result_content.strip()
        if result_content.startswith("```json"):
            result_content = result_content.replace("```json", "", 1)
        if result_content.endswith("```"):
            result_content = result_content[::-1].replace("```", "", 1)[::-1]
            
        result_json = json.loads(result_content)
        
        # Ensure default structure if parsing missed something
        required_keys = ["score", "strengths", "gaps", "recommendation"]
        for key in required_keys:
            if key not in result_json:
                if key == "score": result_json[key] = 0
                elif key in ["strengths", "gaps"]: result_json[key] = []
                elif key == "recommendation": result_json[key] = "Not Fit"
                
        return result_json
        
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return {
            "score": 0,
            "strengths": ["Error analyzing resume"],
            "gaps": [str(e)],
            "recommendation": "Not Fit"
        }
