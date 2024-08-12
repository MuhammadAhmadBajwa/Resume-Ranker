## CV Filtering and Rating System using LLMs

This repository contains a system for filtering and rating CVs based on job descriptions using Large Language Models (LLMs). 

**How it works:**

1. **Job Description Input:** The system takes a job description as input.
2. **LLM Analysis:** The job description is analyzed by an LLM (e.g., GPT-3) to extract key skills, responsibilities, and requirements.
3. **CV Extraction:**  CVs are processed to extract relevant information such as skills, experience, and education.
4. **Matching and Scoring:** The extracted information from the CVs is compared against the job description analysis.

**Features:**

- **Automated CV Analysis:**  Automates the process of analyzing CVs against job descriptions.
- **LLM-Powered:** Uses the capabilities of LLMs for deep understanding of text and context.
- **Efficient Filtering and Ranking:** Streamlines the process of identifying the most suitable candidates.

**Getting Started:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MuhammadAhmadBajwa/Resume-Ranker
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API Keys:**
   - Obtain API keys from https://console.groq.com/keys
   - Replace the API key in the code.
4. **Run the system:**
   ```bash
   py app.py
   ```
   - Go to the generated link

**Screenshots:**

<img alt="Chatbot ScreenShot" src="https://raw.githubusercontent.com/MuhammadAhmadBajwa/Resume-Ranker/main/images/screenshoot1.png">
<img alt="Chatbot ScreenShot" src="https://raw.githubusercontent.com/MuhammadAhmadBajwa/Resume-Ranker/main/images/screenshoot2.png">