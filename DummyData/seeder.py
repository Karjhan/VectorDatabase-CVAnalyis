import os
import requests
import random
import string

API_URL = "http://localhost:8000/upload_cv"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def random_name():
    first = "".join(random.choices(string.ascii_letters, k=6)).capitalize()
    last = "".join(random.choices(string.ascii_letters, k=8)).capitalize()
    return f"{first} {last}"

def random_email(name):
    username = name.lower().replace(" ", ".")
    domain = random.choice(["example.com", "testmail.com", "mailinator.com"])
    return f"{username}@{domain}"

def seed_data():
    for role_folder in os.listdir(DATA_DIR):
        role_path = os.path.join(DATA_DIR, role_folder)
        if not os.path.isdir(role_path):
            continue
        role = role_folder.lower()
        for filename in os.listdir(role_path):
            if not filename.endswith(".pdf"):
                continue

            file_path = os.path.join(role_path, filename)
            name = random_name()
            email = random_email(name)
            print(f"Uploading {filename} as {name} ({email}), role={role}")

            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/pdf")}
                data = {"name": name, "email": email, "role": role}
                try:
                    response = requests.post(API_URL, files=files, data=data)
                    response.raise_for_status()
                    print(f"Uploaded {filename}: {response.json()}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to upload {filename}: {e}")

if __name__ == "__main__":
    seed_data()
