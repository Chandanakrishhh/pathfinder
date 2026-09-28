def priority_score(readiness, days_left):
    return readiness + 30 / days_left


def make_reason(readiness, days_left, rank):
    if rank == 1:
        text = "Act on this first: "
    else:
        text = "Later: "
    text += str(readiness) + "% ready with " + str(days_left) + " days left"
    if readiness < 40 and days_left <= 5:
        text += ". Deadline is close but readiness is low, so this is a risky choice"
    elif readiness >= 70 and days_left <= 5:
        text += ". Good readiness and a close deadline, so act now"
    elif days_left > 10:
        text += ". Enough time to prepare later"
    return text


def prioritize(results, companies):
    info = {c["company_id"]: c for c in companies}
    ranked = []
    for r in results:
        c = info[r["company_id"]]
        score = priority_score(r["readiness"], c["prep_days_left"])
        ranked.append({
            "company_id": r["company_id"],
            "company_name": r["company_name"],
            "readiness": r["readiness"],
            "days_left": c["prep_days_left"],
            "deadline": c["deadline"],
            "missing": r["missing"],
            "priority": round(score, 1)
        })
    ranked.sort(key=lambda x: x["priority"], reverse=True)
    for i, r in enumerate(ranked):
        r["reason"] = make_reason(r["readiness"], r["days_left"], i + 1)
    return ranked
