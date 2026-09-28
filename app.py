import io
import os
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from pipeline.run_pipeline import load, run_pipeline
from agents.readiness_agent import run_readiness
from utils.resume_parser import extract_skills, find_skills, read_pdf
from utils import storage

st.set_page_config(page_title="Path Finder", layout="wide")
st.title("Path Finder")
st.write("A smart assistant for placement guidance")

if "msg" in st.session_state:
    st.success(st.session_state.pop("msg"))

students = load("students.json")
base_companies = load("companies.json")
base_history = load("interview_history.json")
custom, expired = storage.load_custom_companies()
companies = base_companies + custom

all_skills = sorted(
    {s for c in companies for s in c["jd_skills"]} | {s for x in students for s in x["resume_skills"]}
)

STAGES = ["HR", "Technical", "Aptitude", "None (Selected)"]


def canon(skill, known):
    for k in known:
        if k.lower() == skill.lower():
            return k
    return skill[:1].upper() + skill[1:]


def retag(rows, sid):
    return [dict(r, student_id=sid) for r in rows]


def resume_skills(r):
    skills = list(r["skills"])
    try:
        fresh = extract_skills(r["file"], all_skills)
        skills += [s for s in fresh if s not in r["checked_skills"] and s not in skills]
    except FileNotFoundError:
        st.warning("Resume file for " + r["label"] + " is missing. Using saved skills only")
    return skills


def past_interviews():
    count = st.sidebar.number_input("Past interviews", 0, 5, 0)
    rows = []
    for i in range(int(count)):
        c1, c2 = st.sidebar.columns(2)
        ctype = c1.selectbox("Type", ["Service-based", "Product-based"], key="t" + str(i))
        stage = c2.selectbox("Result", STAGES, key="r" + str(i))
        rows.append({
            "company_id": "P" + str(i),
            "company_name": "Past company " + str(i + 1),
            "company_type": ctype,
            "rounds_cleared": 0,
            "total_rounds": 0,
            "drop_off_stage": stage
        })
    return rows


mode = st.sidebar.radio("Choose input", ["Sample student", "Upload new resume", "Saved profile"])
student = None
person = None
user_history = base_history

if mode == "Sample student":
    names = [s["name"] for s in students]
    choice = st.sidebar.selectbox("Select student", names)
    student = students[names.index(choice)]
    st.subheader("Skills on resume")
    st.write(", ".join(student["resume_skills"]))

elif mode == "Upload new resume":
    name = st.sidebar.text_input("Your name")
    label = st.sidebar.text_input("Resume label", value="Main")
    file = st.sidebar.file_uploader("Upload your resume (PDF)", type="pdf")
    if file:
        pdf_bytes = file.getvalue()
        found = extract_skills(io.BytesIO(pdf_bytes), all_skills)
        st.subheader("Skills found in your resume")
        skills = st.multiselect("Edit if anything is wrong", all_skills, default=found)
        past = past_interviews()
        sid = "U_" + storage.slug(name) if name else "UPLOAD"
        student = {"student_id": sid, "name": name or "You", "resume_skills": skills}
        user_history = base_history + retag(past, sid)
        agree = st.sidebar.checkbox("I agree to save my resume on this computer")
        if st.sidebar.button("Save profile"):
            if not name:
                st.sidebar.error("Enter your name first")
            elif not agree:
                st.sidebar.error("Tick the consent box first")
            else:
                label = label.strip() or "Main"
                storage.save_resume(name, label, skills, past, pdf_bytes, all_skills)
                st.session_state["msg"] = "Saved as " + label + ". Open it later from Saved profile"
                st.rerun()
    else:
        st.info("Upload a text-based PDF resume from the sidebar")

else:
    profiles = storage.read_profiles()
    if not profiles:
        st.info("No saved profiles yet. Upload a resume and save it first")
    else:
        names = [p["name"] for p in profiles]
        choice = st.sidebar.selectbox("Select saved profile", names)
        person = profiles[names.index(choice)]
        labels = [r["label"] for r in person["resumes"]]
        label = st.sidebar.selectbox("Resume version", labels)
        r = person["resumes"][labels.index(label)]
        skills = resume_skills(r)
        student = {"student_id": person["student_id"], "name": person["name"], "resume_skills": skills}
        user_history = base_history + retag(person["history"], person["student_id"])
        st.subheader("Skills for " + person["name"] + " (" + label + ")")
        st.write(", ".join(skills))
        if os.path.exists(r["file"]):
            with open(r["file"], "rb") as f:
                st.download_button("Open or download this resume", f.read(), file_name=label + ".pdf", mime="application/pdf")
            with st.expander("What Path Finder read from this resume"):
                st.text(read_pdf(r["file"]))
        st.caption("To add another version, use Upload new resume with the same name and a new label")
        if st.sidebar.button("Delete this resume version", key="del_resume"):
            storage.delete_resume(person["student_id"], label)
            st.session_state["msg"] = "Deleted " + label
            st.rerun()
        if st.sidebar.button("Delete whole profile", key="del_profile"):
            storage.delete_profile(person["student_id"])
            st.session_state["msg"] = "Profile deleted"
            st.rerun()

with st.sidebar.expander("Add a company"):
    with st.form("add_company", clear_on_submit=True):
        cname = st.text_input("Company name", key="c_name")
        role = st.text_input("Role", key="c_role")
        ctype = st.selectbox("Company type", ["Service-based", "Product-based"], key="c_type")
        deadline = st.date_input("Deadline", value=date.today() + timedelta(days=7), min_value=date.today() + timedelta(days=1), key="c_deadline")
        jd_text = st.text_area("Paste job description (optional)", key="c_jd")
        jd_pick = st.multiselect("JD skills", all_skills, key="c_skills")
        extra = st.text_input("Other skills, comma separated", key="c_extra")
        submitted = st.form_submit_button("Add company")
    if submitted:
        picked = list(jd_pick) + find_skills(jd_text, all_skills)
        picked += [canon(x.strip(), all_skills) for x in extra.split(",") if x.strip()]
        skills_jd = list(dict.fromkeys(picked))
        if not cname.strip() or not skills_jd:
            st.error("Enter a company name and at least one skill")
        else:
            storage.add_company(cname.strip(), role.strip() or "Software Engineer", ctype, deadline, skills_jd)
            st.session_state["msg"] = "Added " + cname.strip()
            st.rerun()
    if custom:
        remove = st.selectbox("Remove a company you added", [c["company_name"] for c in custom], key="c_remove")
        if st.button("Remove company"):
            storage.remove_company(remove)
            st.rerun()

if expired:
    st.sidebar.warning("Skipped (deadline passed): " + ", ".join(expired))
st.sidebar.caption("Saved resumes stay in the uploads folder on this computer")

if student:
    st.caption(str(len(companies)) + " companies (" + str(len(custom)) + " added by you)")
    results, ranked, plan = run_pipeline(student, companies, user_history)

    st.header("1. Readiness Agent")
    st.dataframe(pd.DataFrame([{"Company": r["company_name"], "Readiness %": r["readiness"], "Why": r["reason"]} for r in results]), width="stretch", hide_index=True)

    st.header("2. Prioritization Agent")
    st.dataframe(pd.DataFrame([{"Rank": i + 1, "Company": r["company_name"], "Readiness %": r["readiness"], "Days left": r["days_left"], "Priority": r["priority"], "Why": r["reason"]} for i, r in enumerate(ranked)]), width="stretch", hide_index=True)
    st.success("Focus first on: " + ranked[0]["company_name"])

    st.header("3. Interview-Prep Agent")
    st.write("Plan for " + ranked[0]["company_name"])
    st.dataframe(pd.DataFrame([{"Day": p["day"], "Focus": p["focus"], "Practice question": p["practice_question"]} for p in plan]), width="stretch", hide_index=True)

if student and person and len(person["resumes"]) > 1:
    st.header("Which resume fits which company?")
    table = {}
    for rr in person["resumes"]:
        s = {"student_id": person["student_id"], "name": person["name"], "resume_skills": resume_skills(rr)}
        table[rr["label"]] = {x["company_name"]: x["readiness"] for x in run_readiness(s, companies, user_history)}
    df = pd.DataFrame(table)
    df["Best resume"] = df.idxmax(axis=1)
    df.index.name = "Company"
    st.dataframe(df, width="stretch")