"""Rule-based query planning: expand one question into sub-questions.

No LLM is involved. The planner keeps the original question,
adds a keyword-only form (stopwords stripped), and a method
form, so retrieval sees the question from three angles.
"""
import re

STOPWORDS = set("""a an the is are was were what how why when where
which who whom does do did can could should would be been being
of in on for to with by at from as and or it its this that""".split())


def keywords(question):
    words = re.findall(r"[a-z0-9]+", question.lower())
    return [w for w in words if w not in STOPWORDS]


def plan(question):
    question = question.strip()
    keys = keywords(question)
    subs = [question]
    if keys:
        subs.append(" ".join(keys))
        subs.append(" ".join(keys) + " method approach")
    seen, out = set(), []
    for s in subs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out[:3]
