To start the Chatbot do following steps:

1. Activate the virtual Environment with: .\.venv\Scripts\Activate.ps1
2. Change directory to backend folder: cd backend
3. Start the main app: uvicorn main:app --reload --port 5000
4. Open a new terminal window and change directory to frontend folder: cd frontend
5. Start the Webserver: python3 -m http.server 5000
6. Open in Browser: http://localhost:5000
7. For Dashboard, open in Browser: http://localhost:5000/report.html
