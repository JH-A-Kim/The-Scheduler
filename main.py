import os
from flask import Flask, request, jsonify, send_file
from google.cloud import vision
from ics import Calendar, Event
from datetime import datetime, timedelta
import json
import openai
from dotenv import load_dotenv
import io
from ics.grammar.parse import ContentLine
import pytz
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
vision_client = vision.ImageAnnotatorClient()

load_dotenv()
DAYS_MAPPING = {
    "M": 0, "Tu": 1, "W": 2, "Th": 3, "F": 4
}

today=datetime.today()
SEMESTER_START_DATE=today-timedelta(days=today.weekday())

def extract_table_from_image(image_bytes):
    image = vision.Image(content=image_bytes)
    response = vision_client.text_detection(image=image)

    if response.error.message:
        raise Exception(f"Google Vision API error: {response.error.message}")

    words_with_positions = []

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    word_info = {
                        'text': word_text,
                        'bounding_box': word.bounding_box
                    }
                    words_with_positions.append(word_info)

    return words_with_positions

def group_words_into_table(words_with_positions, row_threshold=30, cell_threshold=30):
    words_with_positions.sort(key=lambda x: min(v.y for v in x['bounding_box'].vertices))

    rows = []
    current_row = []
    prev_y = None

    for word_info in words_with_positions:
        y = min(v.y for v in word_info['bounding_box'].vertices)
        if prev_y is None or abs(y - prev_y) < row_threshold:
            current_row.append(word_info)
        else:
            rows.append(current_row)
            current_row = [word_info]
        prev_y = y
    if current_row:
        rows.append(current_row)

    table = []
    for row in rows:
        row.sort(key=lambda word: min(v.x for v in word['bounding_box'].vertices))
        cells = []
        current_cell = [row[0]]
        current_cell_left = min(v.x for v in row[0]['bounding_box'].vertices)
        last_x = current_cell_left 

        for word in row[1:]:
            x = min(v.x for v in word['bounding_box'].vertices)
            if x - last_x > cell_threshold:
                cell_text = " ".join([w['text'] for w in current_cell])
                cells.append(cell_text)
                current_cell = [word]
                current_cell_left = x
                last_x = x
            else:
                current_cell.append(word)
                last_x = x
        if current_cell:
            cell_text = " ".join([w['text'] for w in current_cell])
            cells.append(cell_text)
        table.append(cells)

    return table

def parse_schedule_via_chatgpt(table_data):
    prompt = (
        "You are an expert data parser. Given the following table data as a list of lists:\n\n"
        f"{json.dumps(table_data, indent=2)}\n\n"
        "Convert this into a JSON array of schedule entries with the following keys: "
        '"course", "day", "start_time", "end_time", and "location". '
        "Output only valid JSON some of the information may be disorganized so account for that and also keep an eye on the start and end times, make sure that the start_time is before the end_time. like for example 4:20 PM is after 2:30 PM so we would would want 2:30 as the start time and 4:20 as the end time. And remember to not add anything like markdown fences to mark it as code I want it purely as json. And include the course number in the course name"
    )

    response = openai.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful data parsing assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0)
    return response.choices[0].message.content.strip()

def extract_days(dayString):
    days=[]
    if "M" in dayString:
        days.append("M")
        dayString = dayString.replace("M", "")
    if "Tu" in dayString:
        days.append("Tu")
        dayString = dayString.replace("Tu", "")
    if "W" in dayString:
        days.append("W")
        dayString = dayString.replace("W", "")  
    if "Th" in dayString:
        days.append("Th")
        dayString = dayString.replace("Th", "")
    if "F" in dayString:
        days.append("F")
        dayString = dayString.replace("F", "")
    return days

@app.route("/upload", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        image = file.read()
        words_with_positions = extract_table_from_image(image)
        table = group_words_into_table(words_with_positions)

        schedule_json_str = parse_schedule_via_chatgpt(table)
        
        print(schedule_json_str)
        schedule = json.loads(schedule_json_str)
        print(schedule)
        if not schedule:
            return jsonify({"error": "No schedule entries found."}), 400

        cal = Calendar()

        semester_start=SEMESTER_START_DATE

        pst=pytz.timezone('US/Pacific')

        for entry in schedule:
            day_list = extract_days(entry["day"])
            for day_abbr in day_list:
                target_weekday = DAYS_MAPPING.get(day_abbr)
                if target_weekday is None:
                    continue

                days_ahead = (target_weekday - semester_start.weekday()) % 7
                event_date = semester_start + timedelta(days=days_ahead)

                days_ahead = (target_weekday - semester_start.weekday()) % 7
                event_date = semester_start + timedelta(days=days_ahead)

                start_time = datetime.strptime(entry["start_time"], "%I:%M %p").time()
                end_time = datetime.strptime(entry["end_time"], "%I:%M %p").time()

                start_dt = pst.localize(datetime.combine(event_date.date(), start_time))
                end_dt = pst.localize(datetime.combine(event_date.date(), end_time))


                event = Event(
                    name=entry["course"],
                    begin=start_dt,
                    end=end_dt,
                    location=entry["location"]
                )
                event.extra.append(ContentLine(name="RRULE", params={}, value="FREQ=WEEKLY"))
                event.extra.append(ContentLine(name="BEGIN", params={}, value="VALARM"))
                event.extra.append(ContentLine(name="TRIGGER", params={}, value=f"-PT15M"))
                event.extra.append(ContentLine(name="ACTION", params={}, value="DISPLAY"))
                event.extra.append(ContentLine(name="DESCRIPTION", params={}, value=f"Reminder: {entry['course']} starts soon!"))
                event.extra.append(ContentLine(name="END", params={}, value="VALARM"))
                

                cal.events.add(event)


        ics_content = str(cal)

        ics_bytes = io.BytesIO(ics_content.encode('utf-8'))
        ics_bytes.seek(0)
        return send_file(
            ics_bytes,
            as_attachment=True,
            download_name="schedule.ics",
            mimetype="text/calendar"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
