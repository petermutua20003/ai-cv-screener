AI-Powered CV Screener & Ranker
An automated resume screening tool that parses PDF resumes, extracts key information (skills, experience, education, projects), and ranks candidates against a provided job description using a weighted scoring algorithm.

Overview
Recruiters often have to manually sift through hundreds of resumes for a single role. This Flask-based application automates that initial screening process. Users upload a plain-text job description and multiple PDF resumes. The backend extracts the text, identifies required tech skills from the job description, and scans each resume for those skills alongside experience, education, and project sections. Candidates are then ranked and displayed on a clean, responsive dashboard with a clear match percentage.

Key Features
PDF Text Extraction: Uses PyMuPDF (fitz) to reliably extract plain text from multi-page PDF resumes.
Context-Aware Parsing: Custom regex and string-parsing logic to identify specific resume sections (Experience, Education, Projects) and stitch multi-line bullet points back together.
Weighted Scoring Algorithm: Scores candidates based on a configurable matrix (60% Tech Skills, 15% Experience, 15% Education, 10% Projects).
Concurrent Processing: Uses temporary directories (tempfile) for each request, ensuring multiple users can upload files simultaneously without data collisions.
Secure File Handling: Implements secure_filename and strict file type validation to protect the server.
Responsive Frontend: Vanilla JavaScript and CSS handle file uploads, loading states, and dynamic result rendering without needing a frontend framework.
Tech Stack
Backend: Python, Flask
PDF Parsing: PyMuPDF (fitz)
Frontend: HTML5, CSS3, Vanilla JavaScript (Fetch API)
File Handling: Werkzeug, Tempfile, Shutil
How to Run Locally
Clone the repository: git clone https://github.com/petermutua20003/ai-cv-screener.git
Navigate to the project folder: cd ai-cv-screener
Install the dependencies: pip install -r requirements.txt
Start the Flask server: python app.py
Open your browser and go to: http://127.0.0.1:5000
Usage
Open the web app in your browser.
Upload a plain text (.txt) file containing the job description.
Select one or more PDF resumes to upload.
Click "Rank Candidates" to view the parsed profiles, matched/missing skills, and overall match scores.
