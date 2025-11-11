To start the Chatbot do following steps:

1. Activate the virtual Environment with: .\.venv\Scripts\Activate.ps1
2. Change directory to backend folder: cd backend
3. Start the main app: uvicorn main:app --reload
4. Open a new terminal window and change directory to frontend folder: cd frontend
5. Start the Webserver: python3 -m http.server 5500
6. Open in Browser: http://localhost:5500
