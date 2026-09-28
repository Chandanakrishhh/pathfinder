import json
import os
import re
from datetime import date

PROFILES = "data/profiles.json"
CUSTOM = "data/custom_companies.json"
UPLOADS = "uploads"


def read(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_profile(name, skills, history, pdf_bytes, checked_skills):
    os.makedirs(UPLOADS, exist_ok=True)
    sid = "U_" + slug(name)
    filename = UPLOADS + "/" + sid + ".pdf"
    with open(filename, "wb") as f:
        f.write(pdf_bytes)
    profiles = [p for p in read(PROFILES) if p["student_id"] != sid]
    profiles.append({
        "student_id": sid,
        "name": name,
        "resume_skills": skills,
        "checked_skills": checked_skills,
        "resume_file": filename,
        "history": history
    })
    write(PROFILES, profiles)
    return sid


def delete_profile(sid):
    profiles = read(PROFILES)
    for p in profiles:
        if p["student_id"] == sid and os.path.exists(p["resume_file"]):
            os.remove(p["resume_file"])
    write(PROFILES, [p for p in profiles if p["student_id"] != sid])


def load_custom_companies():
    active = []
    expired = []
    for c in read(CUSTOM):
        days = (date.fromisoformat(c["deadline"]) - date.today()).days
        if days >= 1:
            active.append(dict(c, prep_days_left=days))
        else:
            expired.append(c["company_name"])
    return active, expired


def add_company(name, role, company_type, deadline, skills):
    items = read(CUSTOM)
    n = max([int(c["company_id"][1:]) for c in items] + [0]) + 1
    items.append({
        "company_id": "X" + str(n),
        "company_name": name,
        "role": role,
        "company_type": company_type,
        "jd_skills": skills,
        "deadline": deadline.isoformat()
    })
    write(CUSTOM, items)


def remove_company(name):
    write(CUSTOM, [c for c in read(CUSTOM) if c["company_name"] != name])