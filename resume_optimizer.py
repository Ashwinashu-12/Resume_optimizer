import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import docx
import pdfplumber
import re
import language_tool_python
import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')

# ---------- Resume Extractors ----------
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# ---------- Resume Analyzers ----------
def keyword_match(resume_text, job_description):
    resume_words = set(resume_text.lower().split())
    job_words = set(job_description.lower().split())
    match_count = len(resume_words & job_words)
    return match_count, len(job_words), match_count / len(job_words) * 100

def grammar_check(resume_text):
    tool = language_tool_python.LanguageToolPublicAPI('en-US')
    matches = tool.check(resume_text)
    return len(matches), matches[:5]

def length_analysis(resume_text):
    word_count = len(resume_text.split())
    if word_count < 300:
        return f"Too short ({word_count} words). Add more details.", False
    elif word_count > 800:
        return f"Too long ({word_count} words). Consider trimming.", False
    else:
        return f"Good length ({word_count} words).", True

def check_sections(resume_text):
    sections = ['experience', 'education', 'skills', 'projects', 'certifications']
    found = {section: (section in resume_text.lower()) for section in sections}
    return found

def soft_skills_action_verbs_check(resume_text):
    soft_skills = ['teamwork', 'communication', 'leadership', 'problem solving', 'adaptability']
    action_verbs = ['led', 'created', 'developed', 'implemented', 'achieved']
    found_skills = [skill for skill in soft_skills if skill in resume_text.lower()]
    found_verbs = [verb for verb in action_verbs if verb in resume_text.lower()]
    return found_skills, found_verbs

def bullet_point_consistency(resume_text):
    bullet_lines = [line for line in resume_text.split('\n') if line.strip().startswith(("-", "•"))]
    inconsistent = [line for line in bullet_lines if not re.match(r'^[-•] ', line.strip())]
    return len(bullet_lines), len(inconsistent)

# ---------- GUI App ----------
class ResumeOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Resume Optimizer")
        self.root.geometry("850x650")

        self.resume_path = ""

        tk.Label(root, text="Paste Job Description:", font=('Arial', 11, 'bold')).pack(anchor='w', padx=10)
        self.job_desc_text = scrolledtext.ScrolledText(root, height=6)
        self.job_desc_text.pack(fill='x', padx=10, pady=5)

        self.upload_btn = tk.Button(root, text="Upload Resume (.docx or .pdf)", command=self.upload_resume)
        self.upload_btn.pack(pady=5)

        self.analyze_btn = tk.Button(root, text="Analyze Resume", command=self.analyze)
        self.analyze_btn.pack(pady=5)

        tk.Label(root, text="Optimization Report:", font=('Arial', 11, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        self.results_text = scrolledtext.ScrolledText(root, height=22)
        self.results_text.pack(fill='both', expand=True, padx=10, pady=5)

    def upload_resume(self):
        path = filedialog.askopenfilename(filetypes=[("Resume Files", "*.docx *.pdf")])
        if path:
            self.resume_path = path
            self.upload_btn.config(text=f"Resume Loaded: {path.split('/')[-1]}")

    def analyze(self):
        if not self.resume_path:
            messagebox.showwarning("No Resume", "Please upload a resume file.")
            return

        job_description = self.job_desc_text.get("1.0", tk.END).strip()
        if not job_description:
            messagebox.showwarning("No Job Description", "Please enter a job description.")
            return

        # Extract text
        try:
            if self.resume_path.endswith(".docx"):
                resume_text = extract_text_from_docx(self.resume_path)
            elif self.resume_path.endswith(".pdf"):
                resume_text = extract_text_from_pdf(self.resume_path)
            else:
                messagebox.showerror("Invalid File", "Only .docx and .pdf files are supported.")
                return
        except Exception as e:
            messagebox.showerror("File Error", f"Could not read resume: {str(e)}")
            return

        results = []
        suggestions_needed = False

        # 1. Keyword Match
        match_count, total, percentage = keyword_match(resume_text, job_description)
        results.append(f"🔍 Keyword Match: {match_count}/{total} ({percentage:.2f}%)")
        if percentage < 50:
            suggestions_needed = True
            results.append("❗ Add more job-specific keywords.")

        # 2. Grammar Check
        error_count, issues = grammar_check(resume_text)
        results.append(f"📝 Grammar Issues: {error_count}")
        if error_count > 10:
            suggestions_needed = True
            results.append("❗ Fix grammar to improve professionalism.")
        results.append("Top issues:")
        for issue in issues:
            results.append(f"- {issue.message}")

        # 3. Length
        length_msg, length_ok = length_analysis(resume_text)
        results.append(f"📏 Length: {length_msg}")
        if not length_ok:
            suggestions_needed = True

        # 4. Sections
        sections = check_sections(resume_text)
        results.append("🧩 Resume Sections:")
        for sec, present in sections.items():
            results.append(f"  {sec.title()}: {'✅' if present else '❌'}")
            if not present:
                suggestions_needed = True

        # 5. Soft Skills & Verbs
        skills, verbs = soft_skills_action_verbs_check(resume_text)
        results.append(f"💬 Soft Skills: {', '.join(skills) if skills else 'None found'}")
        results.append(f"🚀 Action Verbs: {', '.join(verbs) if verbs else 'None found'}")
        if not skills or not verbs:
            suggestions_needed = True
            results.append("❗ Add soft skills and action verbs to show impact.")

        # 6. Bullets
        bullets, inconsistents = bullet_point_consistency(resume_text)
        results.append(f"✅ Bullet Points: {bullets} total, {inconsistents} inconsistent")
        if inconsistents > 0:
            suggestions_needed = True
            results.append("❗ Fix inconsistent bullet formatting.")

        # Final Advice
        results.append("\n🔎 Overall Suggestion:")
        if suggestions_needed:
            results.append("🔧 Your resume could use some improvements. See above suggestions.")
        else:
            results.append("🎯 Your resume looks well-optimized for the job description. Great job!")

        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "\n".join(results))


# ---------- Run App ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeOptimizerApp(root)
    root.mainloop()
