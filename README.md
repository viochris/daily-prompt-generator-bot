# 🎨 Daily Prompt Generator Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Prefect](https://img.shields.io/badge/Prefect-Orchestration-070E28?logo=prefect&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Database-34A853?logo=googlesheets&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**Daily Prompt Generator Bot** is a **Prefect-orchestrated automation tool** that acts as your personal AI Art Director.

Designed to fuel your creative workflows, this bot autonomously wakes up every day, uses **Google Gemini 2.5 Flash** to engineer a unique, high-quality image generation prompt (Cyberpunk, Fantasy, Horror, etc.), and securely logs it into a **Google Sheet**. This ensures you always have a fresh queue of creative ideas ready for your AI art generation pipelines.

### 🔗 The "Creative Ecosystem"
This project is designed to work seamlessly with the **[Automated Image Pipeline](https://github.com/viochris/automated-image-pipeline)**.
* **Producer (This Bot):** Generates ideas and *fills* the spreadsheet row by row.
* **Consumer (Image Bot):** Reads from the same spreadsheet, generates the art, and posts it to Telegram.
* **Flexible Scheduling:** You can run them as a single monolithic flow or schedule them sequentially (e.g., Prompt Gen at 06:00, Image Gen at 06:10) to ensure your content queue never runs dry.

### ⚡ Batch Processing (High-Volume Mode)
Need more than one idea per day? Check out the **[Batch Prompt Bot Variant](https://github.com/viochris/daily-batch-prompt-bot)**.
* **3x Efficiency:** Instead of one prompt, the AI generates **3 unique prompts** in a single API call.
* **Smart Parsing:** The AI formats the output with specific delimiters (Double Newlines), which the script automatically splits into a list.
* **Bulk Upload:** Uses `gspread`'s batch insertion features to upload all 3 prompts to the database simultaneously, filling your queue faster with fewer resources.

## ✨ Key Features
### 🧠 Creative AI Engineering
* **Gemini 2.5 Flash Integration:** Leverages the latest Google GenAI SDK to generate descriptive, artistic prompts.
* **Smart Prompting:** Instructs the AI to act as an "Art Director," ensuring output includes subject details, lighting, style keywords, and vibes (e.g., "Cinematic lighting," "Isometric view").

### 📊 Automated Database Management
* **Google Sheets Integration:** Uses `gspread` to connect to a secure spreadsheet database.
* **Workflow Logic:** Appends the newly generated prompt directly to the "Process" worksheet, ready to be picked up by other automation tools (like an Image Generator Bot).

### 🛡️ Robust Orchestration
* **Prefect Flows:** Wraps logic in resilient tasks with automatic **Retry Policies** (3 retries, 5s delay) to handle transient API glitches.
* **Secure Error Handling:** Implements strictly sanitized logging to prevent API keys or credential leaks during runtime errors.
* **Fail-Fast Mechanism:** Automatically halts the flow if the AI returns empty data or if database permissions fail.

## 🛠️ Tech Stack
* **Orchestrator:** Prefect (Workflow Management)
* **Language:** Python 3.11
* **AI Engine:** Google GenAI SDK (`gemini-2.5-flash`)
* **Database:** Google Sheets API (`gspread`)
* **Utilities:** Python-Dotenv

## 🚀 The Automation Pipeline
1.  **Trigger:** Scheduled run (Daily via GitHub Actions or Local Cron).
2.  **Generate (Task 1):** Calls Gemini 2.5 Flash with a specific "Art Director" system instruction to create a unique prompt.
3.  **Validate:** Checks if the output is non-empty and valid text.
4.  **Store (Task 2):** Connects to Google Sheets via Service Account and appends the new prompt to the queue.

## ⚙️ Configuration (Environment Variables)
Create a `.env` file in the root directory:
```ini
GOOGLE_API_KEY=your_gemini_api_key
```
*Note: You also need a `chatbot_key.json` file for Google Service Account credentials to access Sheets.*

## 📦 Local Installation

1. **Clone the Repository**
```bash
git clone https://github.com/viochris/daily-prompt-generator-bot.git
cd daily-prompt-generator-bot
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
# Requires: prefect, gspread, python-dotenv, google-genai
```

3. **Run the Automation**
```bash
python auto-prompt-generate.py
```

### 🖥️ Expected Output
You should see **Prefect** orchestrating the tasks in real-time:
```text
🚀 Starting Image Prompt Generator Flow...
06:00:01.123 | INFO    | Task run 'Generate Image Prompt' - 🎨 Requesting creative prompt from Gemini...
06:00:02.456 | INFO    | Task run 'Generate Image Prompt' - ✅ Generated Prompt: A futuristic cyberpunk street vendor serving neon noodles...
06:00:03.789 | INFO    | Task run 'Append to Spreadsheet' - 📊 Connecting to Google Sheets...
06:00:04.223 | INFO    | Task run 'Append to Spreadsheet' - ✅ Successfully appended prompt: A futuristic cyberpunk street...
06:00:04.556 | INFO    | Flow run 'Image Prompt Generator Flow' - ✅ Flow completed successfully.
```

## 🚀 Deployment Options
This bot supports two release methods depending on your infrastructure:

| Method | Description | Use Case |
| --- | --- | --- |
| **GitHub Actions** | **Serverless.** Uses `cron` scheduling in `.github/workflows/daily_prompt.yml`. Runs on GitHub servers for free. | Best for daily/scheduled runs without paying for a VPS. |
| **Local / VPS** | **Always On.** Uses `main_flow.serve()` to run as a background service on your own server or Docker container. | Best if you need complex triggers or continuous operation. |

---

**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*"Automate the boring stuff, generate the beautiful stuff."*
