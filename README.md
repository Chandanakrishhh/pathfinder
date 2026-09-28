# Path Finder: A Smart Assistant for Placement Guidance

Multi-agent pipeline that tells a student which placement to focus on and how to prepare.

## Agents
| Agent | File | Job |
|---|---|---|
| Readiness | agents/readiness_agent.py | Skill match vs JD, adjusted by past interview history at similar company types |
| Prioritization | agents/prioritization_agent.py | Ranks companies using readiness and days left |
| Interview-Prep | agents/interview_prep_agent.py | Day-by-day plan from skill gaps and past drop-off stages |

## Rules used
- Readiness = skill match % + 5 per past selection - 5 per past drop-off (max -15) at the same company type
- Priority = readiness + 30 / days left

## Folder structure
```
data/        students.json, companies.json, interview_history.json
agents/      the three agents
utils/       resume_parser.py
pipeline/    run_pipeline.py
app.py       Streamlit UI
```

## Run
```
pip install -r requirements.txt
python -m pipeline.run_pipeline
streamlit run app.py
```
Run all commands from the project root.

## Notes
- No model training. Data is only input to rule-based agents.
- Resume parsing works on text PDFs only, not scanned images.
- Uploaded resumes are read in memory and never saved. *.pdf is in .gitignore.
- Sample data is synthetic.
