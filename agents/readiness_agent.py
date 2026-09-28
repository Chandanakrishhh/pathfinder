import json


def load(name):
    with open("data/" + name) as f:
        return json.load(f)


def skill_match(resume_skills, jd_skills):
    have = [r.lower() for r in resume_skills]
    matched = [s for s in jd_skills if s.lower() in have]
    missing = [s for s in jd_skills if s.lower() not in have]
    score = len(matched) / len(jd_skills) * 100
    return score, matched, missing


def history_effect(student_id, company_type, history):
    drops = []
    selected = 0
    for h in history:
        if h["student_id"] == student_id and h["company_type"] == company_type:
            if h["drop_off_stage"].startswith("None"):
                selected += 1
            else:
                drops.append(h["drop_off_stage"])
    change = selected * 5 - min(len(drops) * 5, 15)
    return change, drops, selected


def make_reason(score, missing, drops, selected, company_type):
    if score >= 70:
        text = "strong skill match"
    elif score >= 40:
        text = "average skill match"
    else:
        text = "weak skill match"
    if drops:
        stage = max(set(drops), key=drops.count)
        word = " company" if len(drops) == 1 else " companies"
        text += ", but you dropped at the " + stage + " round in " + str(len(drops)) + " similar " + company_type + word + " before"
    elif selected:
        text += ", and you were selected at a similar " + company_type + " company before"
    else:
        text += ", no similar interview history yet"
    if missing:
        text += ". Missing: " + ", ".join(missing)
    return text


def readiness(student, company, history):
    score, matched, missing = skill_match(student["resume_skills"], company["jd_skills"])
    change, drops, selected = history_effect(student["student_id"], company["company_type"], history)
    final = max(0, min(100, score + change))
    reason = make_reason(score, missing, drops, selected, company["company_type"])
    return {
        "company_id": company["company_id"],
        "company_name": company["company_name"],
        "readiness": round(final),
        "missing": missing,
        "reason": str(round(final)) + "% ready - " + reason
    }


def run_readiness(student, companies, history):
    return [readiness(student, c, history) for c in companies]


if __name__ == "__main__":
    students = load("students.json")
    companies = load("companies.json")
    history = load("interview_history.json")
    for student in students[:3]:
        print(student["name"])
        for r in run_readiness(student, companies, history):
            print(" ", r["company_name"], "-", r["reason"])
        print()
