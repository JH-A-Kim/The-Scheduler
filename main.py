import os
from flask import Flask, request, jsonify
import cv2
import numpy as np
from ics import Calendar, Event
import pytesseract
import re
from datetime import datetime

# #must use subdomain
app = Flask(__name__)

def preprocess_image(file):
    file_bytes = np.frombuffer(file.read(), np.uint8)

    # Decode the image using OpenCV
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    return thresh

@app.route("/upload", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    preprocess_image(file)
    print("Image processed", file)


    # Process the image and generate .ics files
    # This is a placeholder for actual image processing logic
    # For demonstration, we create a dummy event
    cal = Calendar()
    event = Event()
    event.name = "Sample Event"
    event.begin = '2023-10-01 10:00:00'
    event.end = '2023-10-01 11:00:00'
    cal.events.add(event)

    # Convert calendar to .ics format
    ics_content = str(cal)

    return jsonify({"ics_content": ics_content})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
