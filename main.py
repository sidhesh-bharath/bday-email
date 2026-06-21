import os
import json

def load_json(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file)
        return {}

    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def add_birthday(name, dob):
    data = load_json("birthdays.json")
    data[name] = dob
    with open("birthdays.json", 'w') as file:
        json.dump(data, file)

def get_birthdays():
    return load_json("birthdays.json")

def clear_birthdays():
    with open("birthdays.json", 'w') as file:
        json.dump({}, file)