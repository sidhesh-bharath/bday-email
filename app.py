import os
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, render_template, request, redirect, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load credentials from the local .env file
load_dotenv()

app = Flask(__name__)

# --- Email Server Configurations ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        default = {"email": "", "enabled": False}
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default, f)
        return default
    with open(SETTINGS_FILE, 'r') as f:
        try: return json.load(f)
        except: return {"email": "", "enabled": False}

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_json(file_path="birthdays.json"):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file)
        return {}
    with open(file_path, 'r') as file:
        try: return json.load(file)
        except json.JSONDecodeError: return {}

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

# --- Core Email Dispatcher ---
def send_birthday_email(target_email, names_list):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ CONFIG ERROR: SENDER_EMAIL or SENDER_PASSWORD variables are completely missing in your .env file!")
        return False
    if not target_email:
        print("❌ CONFIG ERROR: No recipient alert target email has been entered inside the UI dashboard panel yet.")
        return False
        
    subject = f"🎉 Birthday Alert: {', '.join(names_list)}!"
    body = f"Hello!\n\nThis is a quick heads up that today is the birthday of:\n" + \
           "\n".join([f"• {name}" for name in names_list]) + \
           "\n\nGo send them some love!\n- BDay Email Team"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = target_email

    try:
        print(f"🔄 Attempting secure SMTP bridge connection to {SMTP_SERVER}:{SMTP_PORT} using system sender user {SENDER_EMAIL}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [target_email], msg.as_string())
        print(f"✅ SUCCESS: Birthday verification notification successfully delivered to inbox: {target_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP SERVER TRANSMISSION CRASH: Failed to deliver email layout route. Error detail:\n{e}")
        return False

def daily_birthday_check():
    config = load_settings()
    if not config.get("enabled") or not config.get("email"):
        return
    
    raw_birthdays = load_json()
    celebrants = []
    for name, dob in raw_birthdays.items():
        _, _, status = calculate_birthday_details(dob)
        if status == "today":
            celebrants.append(name)
            
    if celebrants:
        send_birthday_email(config["email"], celebrants)

@app.route('/')
def home():
    raw_birthdays = load_json()
    app_settings = load_settings()
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
    return render_template('index.html', birthdays=processed_birthdays, settings=app_settings)

@app.route('/save-settings', methods=['POST'])
def save_app_settings():
    email = request.form.get('alert_email', '').strip()
    enabled = request.form.get('email_enabled') == 'on'
    save_settings({"email": email, "enabled": enabled})
    return redirect('/')

@app.route('/test-email', methods=['POST'])
def test_email():
    # Capture whatever is currently typed in the box dynamically
    target_email = request.form.get('alert_email', '').strip()
    if not target_email:
        # Fallback to saved state
        config = load_settings()
        target_email = config.get("email")
        
    print(f"🧪 MANUAL TEST INITIATED: Targeting recipient email box -> {target_email}")
    send_birthday_email(target_email, ["Test Connection Success 🎁"])
    return redirect('/')

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

# --- Background Scheduler Loop Guarded Against Flask Re-loader ---
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    print("⏰ Background scheduler initializing engine processes...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=daily_birthday_check, trigger="cron", hour=8, minute=0)
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)