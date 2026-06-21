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

birthdays = load_json("birthdays.json")

while True:
    operation = input("""
BDay Email

1. Add a birthday
2. View all birthdays
3. Clear birthdays
4. Enable/Disable email notifications
Q. Quit
                    
What would you like to do: """)

    if operation == '1':
        name = input("Enter the name: ")
        birthday = input("Enter the birthday (DD-MM-YYYY): ")
        
        if name not in birthdays.keys():
            birthdays[name] = birthday
            with open("birthdays.json", 'w') as file:
                json.dump(birthdays, file, indent=4)

        input(f"""
Added {name}'s birthday on {birthday}...""")

    elif operation == '2':
        if birthdays:
            print("Birthdays:")
            for name, birthday in birthdays.items():
                print(f"{name}: {birthday}")
        else:
            input("""No birthdays found.""")
    
    elif operation == '3':
        confirm = input("Are you sure you want to clear all birthdays? (yes/no): ")
        if confirm.lower() == 'yes':
            birthdays.clear()
            with open("birthdays.json", 'w') as file:
                json.dump(birthdays, file, indent=4)
            input("All birthdays have been cleared...")
        else:
            input("Operation cancelled...")

    elif operation == '4':
        input("Email notifications feature is currently under development...")

    elif operation.lower() == 'q':
        print("Goodbye!")
        break