import os
import shutil
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from matcher import rank_resumes_logic

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB upload cap


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resumes' not in request.files or 'job_desc' not in request.files:
        return jsonify({"error": "Missing files"}), 400

    job_desc_file = request.files['job_desc']
    resumes = request.files.getlist('resumes')

    if not job_desc_file.filename.lower().endswith('.txt'):
        return jsonify({"error": "Job description must be a .txt file"}), 400

    # Each request gets its own temp folder so concurrent uploads don't collide
    temp_dir = tempfile.mkdtemp(prefix="cv_screener_")

    try:
        jd_path = os.path.join(temp_dir, "jd.txt")
        job_desc_file.save(jd_path)

        resume_paths = []
        for resume in resumes:
            if resume.filename.lower().endswith('.pdf'):
                safe_name = secure_filename(resume.filename)
                path = os.path.join(temp_dir, safe_name)
                resume.save(path)
                resume_paths.append(path)

        if not resume_paths:
            return jsonify({"error": "No valid PDF resumes were uploaded"}), 400

        results = rank_resumes_logic(jd_path, resume_paths)

        if not results:
            return jsonify({"error": "No matching tech skills found in the job description"}), 400

        return jsonify(results)

    except UnicodeDecodeError:
        return jsonify({"error": "Couldn't read the job description - make sure it's a plain text file"}), 400

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    app.run(debug=True)