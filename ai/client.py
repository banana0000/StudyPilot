import re
from collections import Counter

class AIServiceError(Exception):
    """Kept for the UI callback contract; local features do not need a remote service."""


def _sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", text) if len(sentence.strip()) > 18]


def _keywords(text):
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]{4,}", text.lower())
    stop = {"this", "that", "with", "from", "have", "will", "your", "they", "their", "about", "into", "document", "business", "which", "when", "where", "were", "been", "also", "than"}
    return [word for word in words if word not in stop]


def _summary(text, limit=3):
    sentences = _sentences(text)
    if not sentences:
        return "The document does not contain enough readable text for a summary."
    frequencies = Counter(_keywords(text))
    ranked = sorted(sentences, key=lambda sentence: sum(frequencies[word] for word in _keywords(sentence)), reverse=True)
    return " ".join(ranked[:limit])


def _dates(text):
    patterns = [r"\b\d{4}-\d{2}-\d{2}\b", r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?\b"]
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.I))
    return list(dict.fromkeys(found))[:8]


def analyze_document(name, text):
    sentences = _sentences(text)
    action_words = ("must", "should", "need to", "action", "review", "approve", "complete", "follow up", "prepare", "send", "deliver", "schedule")
    risk_words = ("risk", "issue", "blocked", "delay", "budget", "concern", "dependency", "urgent", "critical", "failure")
    actions = [sentence for sentence in sentences if any(word in sentence.lower() for word in action_words)][:6]
    risks = [sentence for sentence in sentences if any(word in sentence.lower() for word in risk_words)][:5]
    dates = _dates(text)
    key_points = sorted(sentences, key=len, reverse=True)[:5] if sentences else []
    if not actions:
        actions = ["Review the executive summary and confirm the most important owner and deadline."]
    if not risks:
        risks = ["No explicit risks were detected; validate assumptions with document stakeholders."]
    return {
        "executive_summary": _summary(text),
        "key_points": key_points,
        "action_items": [{"task": action, "owner": "Team", "priority": "High" if any(term in action.lower() for term in ("urgent", "must", "critical")) else "Medium"} for action in actions],
        "deadlines": [{"date": date, "item": "Confirm the related deliverable in the document."} for date in dates] or [{"date": "Not specified", "item": "No explicit deadline detected."}],
        "risks": [{"risk": risk, "severity": "High" if any(term in risk.lower() for term in ("critical", "urgent", "blocked")) else "Medium"} for risk in risks],
        "suggested_next_steps": ["Confirm owners for the identified actions.", "Validate any dates and dependencies with stakeholders.", "Use the Email or Report tab to share the findings."],
    }


def answer_question(name, text, question):
    query_words = set(_keywords(question))
    sentences = _sentences(text)
    lowered_question = question.lower()
    if any(term in lowered_question for term in ("deadline", "due date", "date", "when")):
        dated = [sentence for sentence in sentences if _dates(sentence)]
        if dated:
            return f"Based on {name}: " + " ".join(dated[:3])
    if any(term in lowered_question for term in ("risk", "issue", "concern")):
        risky = [sentence for sentence in sentences if any(word in sentence.lower() for word in ("risk", "issue", "delay", "blocked", "critical", "concern"))]
        if risky:
            return f"Based on {name}: " + " ".join(risky[:3])
    scored = []
    for sentence in sentences:
        score = len(query_words.intersection(_keywords(sentence)))
        if score:
            scored.append((score, sentence))
    scored.sort(reverse=True)
    if scored:
        return f"Based on {name}: " + " ".join(sentence for _, sentence in scored[:3])
    return f"I could not find a direct answer to that question in {name}. Try asking about a specific topic, date, risk, or action mentioned in the document."


def generate_email(name, text, purpose, tone, recipient):
    greeting = f"Hello {recipient}," if recipient else "Hello,"
    return f"Subject: {purpose} — {name}\n\n{greeting}\n\nI am writing to share a {tone.lower()} {purpose.lower()} based on {name}.\n\n{_summary(text, 2)}\n\nRecommended next step: please review the highlighted actions and confirm any owners or deadlines.\n\nBest regards,\nBusinessPilot AI"


def generate_report(name, text, report_type, detail):
    analysis = analyze_document(name, text)
    points = "\n".join(f"- {point}" for point in analysis["key_points"][: max(2, min(5, detail))])
    actions = "\n".join(f"- {item['task']}" for item in analysis["action_items"][: max(1, min(5, detail))])
    risks = "\n".join(f"- {item['risk']}" for item in analysis["risks"][: max(1, min(4, detail))])
    return f"{report_type}\nDocument: {name}\n\nEXECUTIVE SUMMARY\n{analysis['executive_summary']}\n\nKEY FINDINGS\n{points}\n\nRISKS\n{risks}\n\nRECOMMENDED ACTIONS\n{actions}\n\nNEXT STEP\n{analysis['suggested_next_steps'][0]}"


