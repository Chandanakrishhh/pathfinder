import re
import pdfplumber

ALIASES = {
    "DSA": ["dsa", "data structures"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "Operating Systems": ["operating systems", "operating system"],
    "DBMS": ["dbms", "database management"],
    "JavaScript": ["javascript"],
    "Node.js": ["node.js", "nodejs"],
    "Problem Solving": ["problem solving", "problem-solving"]
}


def read_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text


def find_skills(text, skills_list):
    text = text.lower()
    found = []
    for skill in skills_list:
        names = ALIASES.get(skill, [skill.lower()])
        for name in names:
            pattern = r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])"
            if re.search(pattern, text):
                found.append(skill)
                break
    return found


def extract_skills(pdf_file, skills_list):
    return find_skills(read_pdf(pdf_file), skills_list)
