SKILL_TOPICS = {
    "Python": ("Python basics, lists, dictionaries, OOP", "Difference between list and tuple?"),
    "SQL": ("SQL joins, group by, subqueries", "Write a query for the second highest salary"),
    "Git": ("Git commands, branching, merge", "Difference between merge and rebase?"),
    "Problem Solving": ("Logical puzzles and pattern problems", "Solve a river crossing puzzle"),
    "Java": ("Java OOP, collections, exceptions", "Difference between abstract class and interface?"),
    "Spring Boot": ("Spring Boot REST APIs and annotations", "What does @RestController do?"),
    "DSA": ("Arrays, linked lists, trees, sorting", "Reverse a linked list"),
    "Operating Systems": ("Processes, threads, scheduling, deadlock", "What are the conditions for deadlock?"),
    "DBMS": ("Normalization, keys, transactions", "Explain ACID properties"),
    "React": ("React components, props, state, hooks", "Difference between props and state?"),
    "JavaScript": ("JavaScript closures, promises, async", "What is a closure?"),
    "Node.js": ("Node.js event loop and Express basics", "How does the event loop work?"),
    "MongoDB": ("MongoDB documents and queries", "SQL vs NoSQL differences?"),
    "Machine Learning": ("ML algorithms, overfitting, metrics", "Explain bias vs variance"),
    "Deep Learning": ("Neural networks, backpropagation, CNN", "What is backpropagation?"),
    "Django": ("Django models, views, ORM", "Explain the Django MVT pattern"),
    "C++": ("C++ OOP, pointers, STL", "Difference between pointer and reference?"),
    "AWS": ("AWS EC2, S3, IAM basics", "What is the difference between EC2 and S3?")
}

STAGE_TOPICS = {
    "HR": ("HR round practice: self introduction, strengths, weaknesses", "Tell me about yourself"),
    "Technical": ("Technical round mock: explain projects and core subjects", "Walk me through your best project"),
    "Aptitude": ("Aptitude practice: quant, logical, verbal", "Solve a time and work problem")
}


def build_topics(missing, drop_stages):
    topics = []
    for skill in missing:
        if skill in SKILL_TOPICS:
            topics.append(SKILL_TOPICS[skill])
    for stage in drop_stages:
        if stage in STAGE_TOPICS and STAGE_TOPICS[stage] not in topics:
            topics.append(STAGE_TOPICS[stage])
    topics.append(("Full mock interview", "Self introduction plus one technical question"))
    topics.append(("Revise weak areas", "Redo the questions you got wrong"))
    return topics


def make_plan(student_id, top, history, company_type):
    drop_stages = []
    for h in history:
        if h["student_id"] == student_id and h["company_type"] == company_type:
            if not h["drop_off_stage"].startswith("None"):
                drop_stages.append(h["drop_off_stage"])
    topics = build_topics(top["missing"], drop_stages)
    days = top["days_left"]
    if len(topics) > days:
        topics = topics[:days - 1] + [topics[-2]]
    plan = []
    for i, t in enumerate(topics):
        plan.append({"day": i + 1, "focus": t[0], "practice_question": t[1]})
    return plan
