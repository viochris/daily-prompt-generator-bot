import os
import time

# --- Third Party Utilities ---
from dotenv import load_dotenv
import gspread

# --- Orchestration (Prefect) ---
from prefect import flow, task

# --- AI Ecosystem ---
from google import genai

# ==========================================
# CONFIGURATION & CREDENTIALS
# ==========================================
# 1. Environment Setup
# Load environment variables from a .env file.
# This is crucial for local testing to keep secrets out of the codebase.
load_dotenv()

# 2. API Keys & Secrets
# Fetch sensitive credentials securely from the environment system.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

def get_google_sheets():
    # 2. GOOGLE SHEETS SETUP
    # Authenticate using the service account JSON file
    gc = gspread.service_account("chatbot_key.json")

    # Open the specific Spreadsheet by name
    sh = gc.open("Image Prompt")

    # Define the specific worksheets (tabs) to work with
    ws_process = sh.worksheet("Process")
    ws_done = sh.worksheet("Done")

    return ws_process, ws_done

@task(name="Generate Image Prompt", retries=3, retry_delay_seconds=5)
def generate_image_prompt():
    """
    Task to generate a single, creative image generation prompt using Gemini.
    
    The output is strictly formatted for direct insertion into a Spreadsheet 
    (no markdown, no quotes, just the prompt text).
    """
    
    # 1. System Instruction & Prompt Engineering
    # We give clear examples to guide the style (Descriptive + Keywords).
    prompt_instruction = """
    You are an expert AI Art Director.
    Your task is to generate EXACTLY ONE creative image prompt.

    ### 🎨 STYLE GUIDELINES:
    1. **Structure:** A descriptive main subject followed by comma-separated artistic keywords (lighting, style, vibe).
    2. **Creativity:** Choose a random theme (Cyberpunk, Fantasy, Horror, Realistic, or Abstract).
    3. **Format:** Output ONLY the raw text. Do not use quotes (""), do not use Markdown (**), do not add introductory text.

    ### 💡 EXAMPLES (Follow this pattern):
    - A rice field terrace in Bali but in a floating island setting, waterfalls falling into the void, fantasy art style, vibrant colors.
    - A silhouette of a woman standing at the end of a dark hallway, glowing eyes in the shadow, holding a lantern, horror mystery vibe, cinematic lighting.
    - Isometric view of a dream gaming room, RGB lighting, shelves full of robot figures, cozy atmosphere, digital art, 4k render.

    ### 🚀 YOUR TASK:
    Generate 1 new, unique image prompt now.
    """

    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # 2. Call Gemini Model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_instruction
        )

        # 3. Response Validation
        # Check if the response object exists and has text content.
        if response.text and len(response.text.strip()) > 0:
            cleaned_prompt = response.text.strip()
            print(f"✅ Generated Prompt: {cleaned_prompt}")
            return cleaned_prompt
        
        else:
            print("⚠️ Warning: Gemini returned an empty response.")
            raise Exception("Prompt Generation Failed: Empty Output")

    except Exception as e:
        # 4. Secure Error Handling (Prevent API Key Leakage)
        # Convert the error to a lowercase string for safe analysis.
        error_str = str(e).lower()
        final_error_message = ""

        # Check for specific error types without printing the raw 'e' variable.
        if "quota" in error_str or "429" in error_str:
            final_error_message = "⏳ Error: Google AI API Quota Exceeded."
        
        elif "api_key" in error_str or "403" in error_str or "permission" in error_str:
            final_error_message = "🔑 Error: Google API Key is invalid or restricted."

        elif "timeout" in error_str or "deadline" in error_str:
            final_error_message = "⏱️ Error: Request to Gemini timed out."

        elif "safety" in error_str or "blocked" in error_str:
            final_error_message = "🛡️ Error: AI response was blocked by safety filters."

        else:
            # Fallback for unknown errors (Network, DNS, etc.)
            final_error_message = "❌ Error: Prompt generation failed due to a system issue."

        # Print ONLY the sanitized message to the logs.
        print(final_error_message)

        # Raise the exception to trigger Prefect's retry mechanism.
        raise Exception(final_error_message)

@task(name="Append to Spreadsheet", retries=3, retry_delay_seconds=5)
def to_spreadsheet(prompt_text):
    """
    Task to append the generated text to the Google Spreadsheet.
    
    This function validates the input and securely writes the data to the 
    specified worksheet. It handles API errors without exposing sensitive 
    credentials in the logs.
    """
    try:
        # 1. Spreadsheet Connection
        # Retrieve the worksheet objects.
        ws_process, ws_done = get_google_sheets()

        # 2. Data Validation
        # Ensure the prompt text is valid and not empty before writing.
        if prompt_text is not None and len(prompt_text.strip()) > 0:
            
            # 3. Write Operation
            # Append the data as a new row.
            ws_process.append_row([prompt_text])
            print(f"✅ Successfully appended prompt: {prompt_text[:30]}...")
            
        else:
            print("⚠️ Warning: Prompt text is empty or None.")
            raise Exception("Spreadsheet Error: Empty Input Data")

    except Exception as e:
        # 4. Secure Error Handling
        # Convert exception to string for safe analysis.
        error_str = str(e).lower()
        final_error = ""

        # Handle specific Google API errors (Quota, Permissions, Network).
        if "quota" in error_str or "429" in error_str:
            final_error = "⏳ Error: Google Sheets API Quota Exceeded."

        elif "permission" in error_str or "403" in error_str:
            final_error = "🔑 Error: Google Sheets Permission Denied or Invalid Credentials."

        elif "not found" in error_str or "404" in error_str:
            final_error = "❌ Error: Target Worksheet or Spreadsheet ID not found."

        elif "transport" in error_str or "ssl" in error_str or "connect" in error_str:
            final_error = "🌐 Error: Network connection to Google API failed."

        else:
            # Generic Fallback for unknown errors.
            final_error = f"❌ Error: Spreadsheet update failed due to a system issue -> {e}."

        # Log ONLY the sanitized error message to the console.
        print(final_error)

        # Raise the clean exception to trigger Prefect's retry mechanism.
        raise Exception(final_error)

@flow(name="Image Prompt Generator Flow", log_prints=True)
def main_flow():
    """
    Main orchestration flow for the Image Prompt Generator.
    
    This flow executes the generation task using Gemini and subsequently 
    appends the valid output to the Google Spreadsheet. It serves as the 
    central control unit for the automation process.
    """
    try:
        # 1. Execution Phase
        # Trigger the prompt generation task.
        prompt_text = generate_image_prompt()

        # 2. Validation Phase
        # Ensure the generated text is valid before attempting to save.
        if prompt_text is not None and len(prompt_text.strip()) > 0:
            
            # 3. Storage Phase
            # Send the validated data to the spreadsheet task.
            to_spreadsheet(prompt_text)
            print("✅ Flow completed successfully.")
            
        else:
            # Handle cases where the generator returned None or empty strings.
            print("⚠️ Flow Interrupted: Generated prompt is invalid.")
            raise Exception("Flow Error: Generator returned empty data.")

    except Exception as e:
        # 4. Secure Flow-Level Error Handling
        # Capture any unhandled exceptions from sub-tasks or the flow logic.
        error_str = str(e).lower()
        final_error = ""

        # Categorize errors to provide clear logs without leaking credentials.
        if "quota" in error_str or "429" in error_str:
            final_error = "⏳ Flow Halted: API Quota Exceeded in sub-task."

        elif "permission" in error_str or "403" in error_str:
            final_error = "🔑 Flow Halted: Authentication or Permission error."

        elif "timeout" in error_str:
            final_error = "⏱️ Flow Halted: Sub-task timed out."

        elif "spreadsheet" in error_str:
             final_error = "📊 Flow Halted: Spreadsheet operation failed."

        else:
            # Generic fallback for unexpected flow crashes.
            final_error = "❌ Flow Failed: An unexpected system error occurred."

        # Log the sanitized error message.
        print(final_error)

        # Raise the exception to mark the Flow run as Failed in Prefect UI.
        raise Exception(final_error)

if __name__ == "__main__":
    # ==========================================
    # 🚀 EXECUTION MODE
    # ==========================================

    # --- OPTION 1: FOR GITHUB ACTIONS (ACTIVE) ---
    # This calls the function immediately (Run Once).
    # GitHub's YAML scheduler handles the timing (CRON).
    # When finished, the script exits to save server resources.
    main_flow()

    # --- OPTION 2: FOR LOCAL SERVER / VPS (COMMENTED OUT) ---
    # Use this if you run the script on your own laptop or a 24/7 server.
    # The '.serve()' method keeps the script running indefinitely 
    # and handles the scheduling internally.
    
    # main_flow.serve(
    #     name="deployment-daily-image-generator",
    #     # cron="0 7 * * *", # Run daily at 07:00 AM (server time)
    #     interval=60,        # Or run every 60 seconds (for testing)
    #     tags=["ai", "daily"]
    # )
