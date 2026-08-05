import os
import re
from extractor import get_resume_text

TECH_SKILLS = {
    "python", "javascript", "java", "c++", "sql", "mysql", "postgresql", "mongodb",
    "html", "css", "react", "node.js", "machine learning", "deep learning",
    "computer vision", "natural language processing", "nlp", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "opencv", "keras", "flask", "fastapi",
    "django", "git", "docker", "cnn", "rnn", "gpt"
}

SECTION_STOP_WORDS = [
    "education", "academic", "qualifications", "university",
    "experience", "employment", "work history",
    "project", "portfolio", "personal project", "key project",
    "skills", "technologies", "tools", "competencies",
    "references", "hobbies", "interests", "certifications"
]

# Scoring weights - tech skills carry the most weight since that's usually
# what recruiters filter on first, experience/education/projects fill in the rest
TECH_WEIGHT = 60
EXPERIENCE_WEIGHT = 15
EDUCATION_WEIGHT = 15
PROJECT_WEIGHT = 10


def get_section_bullets(text, section_keywords):
    """Finds a section header in the resume and pulls out the bullet points under it."""
    text_lines = text.split('\n')
    start_index = -1

    # 1. Find where the section starts
    for i, line in enumerate(text_lines):
        line_clean = re.sub(r'[^a-zA-Z\s]', '', line).strip().lower()
        if len(line_clean) < 40:
            for word in section_keywords:
                if word in line_clean:
                    start_index = i
                    break
        if start_index != -1:
            break

    if start_index == -1:
        return []

    # 2. Grab lines until we hit the next section header. Blank lines get kept as
    # a "" marker instead of being dropped - a blank line usually means the resume
    # moved on to a new job/entry, and we need that signal in step 3 below.
    section_lines = []
    for j in range(start_index + 1, len(text_lines)):
        line = text_lines[j].strip()
        if not line:
            section_lines.append("")
            continue

        line_clean = re.sub(r'[^a-zA-Z\s]', '', line).lower()
        is_new_header = False
        if len(line_clean) < 40:
            for stop_word in SECTION_STOP_WORDS:
                if stop_word in line_clean:
                    is_new_header = True
                    break
        if is_new_header:
            break

        section_lines.append(line)

    # 3. Some PDFs split a single bullet point across multiple lines - stitch them
    # back together so a bullet reads as one sentence instead of three fragments.
    # A blank line forces the next line to start a fresh bullet, even if it doesn't
    # start with a bullet symbol or capital letter (e.g. a new job's title line).
    cleaned_bullets = []
    current_bullet = ""
    force_new_bullet = False

    for line in section_lines:
        if line == "":
            force_new_bullet = True
            continue

        # a wrapped continuation line almost never follows a bullet that already
        # ended in a period - if it did end in one, this is a fresh entry (like a
        # new job's title line) even without a blank line separating them
        prev_looks_finished = current_bullet.rstrip().endswith(('.', '!', '?'))

        is_new_point = (
            bool(re.match(r'^[-•*\d\.]', line))
            or (current_bullet == "" and line[0].isupper())
            or force_new_bullet
            or (prev_looks_finished and line[0].isupper())
        )
        force_new_bullet = False

        if is_new_point:
            if current_bullet:
                cleaned_bullets.append(current_bullet.strip())
            current_bullet = re.sub(r'^[-•*\d\.]\s*', '', line)
        else:
            current_bullet += " " + line

    if current_bullet:
        cleaned_bullets.append(current_bullet.strip())

    return cleaned_bullets


def format_bullets_for_ui(bullets, max_bullets=None):
    """Cleans up the raw bullets into a readable list for the UI.

    Unlike before, this keeps every bullet found (not just the first two) so a
    candidate with three jobs listed under Experience doesn't get cut down to one.
    Pass max_bullets if you want to cap it - Education still only shows one line
    since that's usually just "Degree, School" and doesn't need a list.
    """
    if not bullets:
        return "Not detected"

    valid_bullets = [b for b in bullets if len(b) > 15]  # skip junk fragments

    if not valid_bullets:
        return "Not detected"

    if max_bullets:
        valid_bullets = valid_bullets[:max_bullets]

    # each point on its own line, formatted as a proper bullet list
    formatted = []
    for point in valid_bullets:
        if not point.endswith('.'):
            point += "."
        formatted.append(f"• {point}")

    return "\n".join(formatted)


def extract_keywords(text):
    text_lower = text.lower()

    tech = [s for s in TECH_SKILLS if s in text_lower]

    exp_bullets = get_section_bullets(text, ["experience", "work experience", "employment"])
    edu_bullets = get_section_bullets(text, ["education", "academic background", "qualifications"])
    proj_bullets = get_section_bullets(text, ["project", "key project", "personal project", "portfolio"])

    exp_context = format_bullets_for_ui(exp_bullets)
    edu_context = format_bullets_for_ui(edu_bullets, max_bullets=1)
    proj_context = format_bullets_for_ui(proj_bullets)

    exp = ["found"] if exp_bullets else []
    edu = ["found"] if edu_bullets else []
    proj = ["found"] if proj_bullets else []

    return tech, exp, edu, proj, exp_context, edu_context, proj_context


def score_resume(resume_text, required_tech):
    """Runs one resume against the required skill list and returns its full result dict."""
    r_tech, r_exp, r_edu, r_proj, exp_ctx, edu_ctx, proj_ctx = extract_keywords(resume_text)
    matched_tech = [s for s in required_tech if s in r_tech]
    missing_tech = [s for s in required_tech if s not in r_tech]

    tech_score = (len(matched_tech) / len(required_tech)) * TECH_WEIGHT if required_tech else 0
    exp_score = EXPERIENCE_WEIGHT if r_exp else 0
    edu_score = EDUCATION_WEIGHT if r_edu else 0
    proj_score = PROJECT_WEIGHT if r_proj else 0

    final_score = round(tech_score + exp_score + edu_score + proj_score, 1)

    return {
        "score": final_score,
        "matched": sorted(matched_tech),
        "missing": sorted(missing_tech),
        "exp_context": exp_ctx,
        "edu_context": edu_ctx,
        "proj_context": proj_ctx
    }


def get_required_skills(job_text):
    return sorted(s for s in TECH_SKILLS if s in job_text.lower())


def rank_resumes_logic(jd_path, pdf_files):
    """Used by the Flask app - takes a job description path and a list of resume
    PDF paths, and returns a ranked list of candidate results."""
    with open(jd_path, 'r', encoding='utf-8') as f:
        job_text = f.read()

    required_tech = get_required_skills(job_text)
    if not required_tech:
        return []

    results = []
    for pdf_path in pdf_files:
        resume_text = get_resume_text(pdf_path)
        if not resume_text:
            continue

        result = score_resume(resume_text, required_tech)
        result["name"] = os.path.basename(pdf_path)
        results.append(result)

    results.sort(key=lambda x: x['score'], reverse=True)
    return results


def rank_resumes(job_desc_path, resume_folder):
    """CLI entry point - scans a folder of PDFs and prints the ranking to the terminal."""
    pdfs = [f for f in os.listdir(resume_folder) if f.lower().endswith('.pdf')]
    pdf_paths = [os.path.join(resume_folder, pdf) for pdf in pdfs]

    if not pdfs:
        print("No resumes found in", resume_folder)
        return

    results = rank_resumes_logic(job_desc_path, pdf_paths)

    if not results:
        print("No matching tech skills found in the job description, or none of the resumes could be read.")
        return

    print(f"Analyzing against: {job_desc_path}\n")
    print("--- CANDIDATE RANKING ---")

    for res in results:
        print(f"\n[{res['score']}% Match] - {res['name']}")
        print(f"  Exp: {res['exp_context']}")
        print(f"  Edu: {res['edu_context']}")
        print(f"  Proj: {res['proj_context']}")


if __name__ == "__main__":
    rank_resumes("sample_data/job_description.txt", "sample_data/")