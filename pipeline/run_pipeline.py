import json
from agents.readiness_agent import run_readiness
from agents.prioritization_agent import prioritize
from agents.interview_prep_agent import make_plan


def load(name):
    with open("data/" + name) as f:
        return json.load(f)


def run_pipeline(student, companies, history):
    results = run_readiness(student, companies, history)
    ranked = prioritize(results, companies)
    top = ranked[0]
    company = [c for c in companies if c["company_id"] == top["company_id"]][0]
    plan = make_plan(student["student_id"], top, history, company["company_type"])
    return results, ranked, plan


if __name__ == "__main__":
    students = load("students.json")
    companies = load("companies.json")
    history = load("interview_history.json")
    student = students[0]
    results, ranked, plan = run_pipeline(student, companies, history)
    print("Student:", student["name"])
    print()
    print("READINESS")
    for r in results:
        print(" ", r["reason"])
    print()
    print("PRIORITY")
    for r in ranked:
        print(" ", r["company_name"], r["priority"], "-", r["reason"])
    print()
    print("PREP PLAN for", ranked[0]["company_name"])
    for p in plan:
        print("  Day", p["day"], "-", p["focus"], "| Q:", p["practice_question"])
