import io
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from pipeline.run_pipeline import load, run_pipeline
from utils.resume_parser import extract_skills, find_skills
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
user_history = base_history

if mode == "Sample student":
    names = [s["name"] for s in students]
    choice = st.sidebar.selectbox("Select student", names)
    student = students[names.index(choice)]
    st.subheader("Skills on resume")
    st.write(", ".join(student["resume_skills"]))

elif mode == "Upload new resume":
    name = st.sidebar.text_input("Your name")
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
                storage.save_profile(name, skills, past, pdf_bytes, all_skills)
                st.session_state["msg"] = "Profile saved. Open it later from Saved profile"
                st.rerun()
    else:
        st.info("Upload a text-based PDF resume from the sidebar")

else:
    profiles = storage.read(storage.PROFILES)
    if not profiles:
        st.info("No saved profiles yet. Upload a resume and save it first")
    else:
        names = [p["name"] for p in profiles]
        choice = st.sidebar.selectbox("Select saved profile", names)
        p = profiles[names.index(choice)]
        skills = list(p["resume_skills"])
        try:
            fresh = extract_skills(p["resume_file"], all_skills)
            skills += [s for s in fresh if s not in p["checked_skills"] and s not in skills]
        except FileNotFoundError:
            st.warning("Saved resume file is missing. Using saved skills only")
        student = {"student_id": p["student_id"], "name": p["name"], "resume_skills": skills}
        user_history = base_history + retag(p["history"], p["student_id"])
        st.subheader("Skills for " + p["name"])
        st.write(", ".join(skills))
        st.caption("Resume file: " + p["resume_file"])
        if st.sidebar.button("Delete this profile and resume"):
            storage.delete_profile(p["student_id"])
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