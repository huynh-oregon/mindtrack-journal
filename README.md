MindTrack Journal 
MindTrack Journal is a microservices-based journaling application that allows users to write, edit, delete, and export journal entries. The application integrates four microservices (A, B, C, D) for specific functionalities, connected via HTTP requests without direct function imports.
Features
1. Write a new journal entry with optional encouragement text.
2. Edit existing journal entries, including text, encouragement, date, and time.
3. Delete journal entries.
4. Live word count powered by Microservice A.
5. Random encouragement generator powered by Microservice B.
6. Display total journal count with date via Microservice C.
7. Export all journal entries to CSV file using Microservice D.
Microservices
Microservice A - Word Count: Calculates and returns word count for given text.
Microservice B - Encouragement: Returns a random encouragement string.
Microservice C - Count: Returns the total count of saved entries with date.
Microservice D - Export: Generates a CSV file of all entries and returns its path.
Technology Stack
• Python 3
• Flask (for UI and microservices)
• HTML/CSS/JavaScript (frontend)
• HTTP communication between services (requests library)
How to Run
1. Clone the repository to your local machine.
2. Create and activate a Python virtual environment:
   python3 -m venv .venv   source .venv/bin/activate
3. Install dependencies:
   pip install flask requests
4. Start each microservice and the UI server in separate terminals:
   python a_wordcount.py   python b_encouragement.py   python c_count.py   python d_export.py   python ui_app.py
5. Open http://localhost:8080 in your browser to use the application.
Communication Between Main Program and Microservices
The UI server communicates with each microservice via HTTP requests using the `requests` library. No microservice code is imported into the main program; all interactions happen programmatically over defined API endpoints.
