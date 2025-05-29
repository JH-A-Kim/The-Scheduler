# The Scheduler

**The Scheduler** is a Python-based Flask web application that converts images of timetable tables into a recurring calendar schedule (.ics file).

When you upload an image containing a course schedule table:
1. The app uses the Google Cloud Vision API to detect and extract text blocks from the image.
2. It organizes the detected text into a table structure (rows and cells).
3. It sends the table data to the OpenAI API (GPT-3.5-turbo) to parse it into structured JSON schedule entries.
4. It generates an iCalendar (.ics) file with weekly recurring events for each course, complete with 15-minute reminder alarms.

## Features
- **Image-to-Table Extraction**: Uses Google Vision to perform text detection on uploaded images.  
- **Table Parsing**: Dynamically groups words into table rows and cells based on bounding box positions.  
- **AI-powered Parsing**: Leverages OpenAI to convert raw table data into clean JSON schedule entries.  
- **Calendar Generation**: Produces a .ics file with recurring events and reminders in US/Pacific timezone.  
- **Docker & Docker Compose**: Easily containerize and deploy the application.

## Prerequisites
- Python 3.9+ installed  
- [Google Cloud project](https://console.cloud.google.com/) with Vision API enabled  
- Google Cloud service account key or API key with Vision API access  
- OpenAI API key  
- Docker & Docker Compose (for containerized setup)

## Environment Variables
Create a `.env` file in the project root with the following:
```dotenv
GOOGLE_API_KEY=your_google_vision_api_key
OPENAI_API_KEY=your_openai_api_key
PORT=5001          # Optional: defaults to 5001
