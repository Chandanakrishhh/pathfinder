import streamlit as st
import pandas as pd
from pipeline.run_pipeline import load, run_pipeline
from utils.resume_parser import extract_skills

st.set_page_config(page_title="Path Finder", layout="wide")
st.title("Path Finder")
st.write("A smart assistant for placement guidance")

students = load("students.json")
companies = load("companies.json")
history = load("interview_history.json")

all_skills = sorted({s for c in companies for s in c["jd_skills"]} | {s for st_ in students for s in st_["resume_skills"]})

mode = st.sidebar.radio("Choose input", ["Sample student", "Upload resume"])

student = None
user_history = history

if mode == "Sample student":
    names = [s["name"] for s in students]
    choice = st.sidebar.selectbox("Select student", names)
    student = students[names.index(choice)]
    st.subheader("Skills on resume")
    st.write(", ".join(student["resume_skills"]))
else:
    file = st.sidebar.file_uploader("Upload your resume (PDF)", type="pdf")
    if file:
        found = extract_skills(file, all_skills)
        st.subheader("Skills found in your resume")
        skills = st.multiselect("Edit if anything is wrong", all_skills, default=found)
        count = st.sidebar.number_input("Past interviews", 0, 5, 0)
        user_history = []
        for i in range(int(count)):
            col1, col2 = st.sidebar.columns(2)
            ctype = col1.selectbox("Type", ["Service-based", "Product-based"], key="t" + str(i))
            stage = col2.selectbox("Result", ["HR", "Technical", "Aptitude", "None (Selected)"], key="r" + str(i))
            user_history.append({
                "student_id": "UPLOAD",
                "company_id": "P" + str(i),
                "company_name": "Past company " + str(i + 1),
                "company_type": ctype,
                "rounds_cleared": 0,
                "total_rounds": 0,
                "drop_off_stage": stage
            })
        student = {"student_id": "UPLOAD", "name": "You", "resume_skills": skills}
    else:
        st.info("Upload a text-based PDF resume from the sidebar")

if student:
    results, ranked, plan = run_pipeline(student, companies, user_history)

    st.header("1. Readiness Agent")
    st.dataframe(pd.DataFrame([{"Company": r["company_name"], "Readiness %": r["readiness"], "Why": r["reason"]} for r in results]), width="stretch", hide_index=True)

    st.header("2. Prioritization Agent")
    st.dataframe(pd.DataFrame([{"Rank": i + 1, "Company": r["company_name"], "Readiness %": r["readiness"], "Days left": r["days_left"], "Priority": r["priority"], "Why": r["reason"]} for i, r in enumerate(ranked)]), width="stretch", hide_index=True)
    st.success("Focus first on: " + ranked[0]["company_name"])

    st.header("3. Interview-Prep Agent")
    st.write("Plan for " + ranked[0]["company_name"])
    st.dataframe(pd.DataFrame([{"Day": p["day"], "Focus": p["focus"], "Practice question": p["practice_question"]} for p in plan]), width="stretch", hide_index=True)
