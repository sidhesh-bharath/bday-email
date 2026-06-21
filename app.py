import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_file

app = Flask(__name__)

def load_json(file_path="birthdays.json"):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file)
        return {}
    with open(file_path, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def save_json(data, file_path="birthdays.json"):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def calculate_birthday_details(dob_str):
    try:
        birth_date = datetime.strptime(dob_str, "%d-%m-%Y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        next_bday = birth_date.replace(year=today.year)
        if today > next_bday:
            next_bday = next_bday.replace(year=today.year + 1)
        days_left = (next_bday - today).days
        formatted_date = birth_date.strftime("%B %d")
        
        if days_left == 0:
            return "TODAY", formatted_date, "today"
        elif days_left == 1:
            return "TOMORROW", formatted_date, "tomorrow"
        else:
            return f"{days_left}", formatted_date, "normal"
    except ValueError:
        return "—", dob_str, "normal"

@app.route('/')
def home():
    raw_birthdays = load_json()
    processed_birthdays = []
    for name, dob in raw_birthdays.items():
        days_label, formatted_date, status = calculate_birthday_details(dob)
        processed_birthdays.append({
            "name": name,
            "date": formatted_date,
            "days_label": days_label,
            "status": status,
            "sort_key": 0 if status == "today" else (1 if status == "tomorrow" else int(days_label))
        })
    processed_birthdays.sort(key=lambda x: x['sort_key'])
    return render_template('index.html', birthdays=processed_birthdays)

@app.route('/submit-form', methods=['POST'])
def handle_form():
    form_name = request.form.get('name')
    form_dob = request.form.get('dob')
    if form_name and form_dob:
        data = load_json()
        data[form_name] = form_dob
        save_json(data)
    return redirect('/')

@app.route('/clear-birthdays', methods=['POST'])
def clear_birthdays():
    save_json({})
    return redirect('/')

@app.route('/export-birthdays')
def export_birthdays():
    if not os.path.exists("birthdays.json"):
        save_json({})
    return send_file("birthdays.json", as_attachment=True, download_name="birthdays_backup.json")

@app.route('/import-birthdays', methods=['POST'])
def import_birthdays():
    if 'backup_file' not in request.files:
        return redirect('/')
    file = request.files['backup_file']
    if file.filename == '':
        return redirect('/')
    if file:
        try:
            uploaded_data = json.load(file)
            current_data = load_json()
            current_data.update(uploaded_data)
            save_json(current_data)
        except Exception:
            pass
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)