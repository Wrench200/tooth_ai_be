questions = [
    "What’s your business idea, and what problem does it solve for people?",
    "If your brand were wildly successful in 10 years, what would the world look like?",
    "What are three words you want people to associate with your brand — and why?",
    "Describe your ideal customer — who are they, what are they struggling with, and how does your brand help?",
    "Who else is solving this problem, and what makes your solution different or better?",
    "What name do you want for your brand? Why did you choose it?",
    "What’s the boldest promise your brand can confidently make to its customers?",
    "How should your brand look and feel visually? (e.g., playful, elegant, bold, modern, classic, etc.)",
    "Where will your audience mostly interact with your brand? (Instagram, WhatsApp, TikTok, LinkedIn, etc.)",
    "What’s the main thing you want people to do when they see your content? (Trust you? Buy? Follow?)"
]


def get_question(question_number):
    if 1 <= question_number <= len(questions):
        return questions[question_number - 1]
    return "Question not found."


def get_previous_questions(limit_question_number):
    return questions[:limit_question_number - 1] if limit_question_number > 1 else []

