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


def read_profiles():
    profiles = read(PROFILES)
    for p in profiles:
        if "resumes" not in p:
            p["resumes"] = [{
                "label": "Main",
                "file": p.pop("resume_file"),
                "skills": p.pop("resume_skills"),
                "checked_skills": p.pop("checked_skills")
            }]
    return profiles


def save_resume(name, label, skills, history, pdf_bytes, checked_skills):
    os.makedirs(UPLOADS, exist_ok=True)
    sid = "U_" + slug(name)
    filename = UPLOADS + "/" + sid + "_" + (slug(label) or "resume") + ".pdf"
    with open(filename, "wb") as f:
        f.write(pdf_bytes)
    entry = {"label": label, "file": filename, "skills": skills, "checked_skills": checked_skills}
    profiles = read_profiles()
    person = None
    for p in profiles:
        if p["student_id"] == sid:
            person = p
    if person is None:
        person = {"student_id": sid, "name": name, "resumes": [], "history": history}
        profiles.append(person)
    person["resumes"] = [r for r in person["resumes"] if r["label"] != label] + [entry]
    if history:
        person["history"] = history
    write(PROFILES, profiles)
    return sid


def delete_resume(sid, label):
    profiles = read_profiles()
    for p in profiles:
        if p["student_id"] == sid:
            for r in p["resumes"]:
                if r["label"] == label and os.path.exists(r["file"]):
                    os.remove(r["file"])
            p["resumes"] = [r for r in p["resumes"] if r["label"] != label]
    write(PROFILES, [p for p in profiles if p["resumes"]])


def delete_profile(sid):
    profiles = read_profiles()
    for p in profiles:
        if p["student_id"] == sid:
            for r in p["resumes"]:
                if os.path.exists(r["file"]):
                    os.remove(r["file"])
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