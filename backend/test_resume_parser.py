from app.services.resume_parser import extract_resume_text

file_path = "uploads/resumes/eddad9b1-caeb-4077-9396-6efae9a8659b.pdf"

text = extract_resume_text(file_path)

print("\n========== EXTRACTED RESUME TEXT ==========\n")
print(text)
print("\n============================================")
print(f"\nCharacters extracted: {len(text)}")