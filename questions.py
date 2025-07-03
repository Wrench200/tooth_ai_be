form_questions = {
  "sections": [
    {
      "section_number": 1,
      "section_title": "brand_strategy",
      "questions": [
        {
          "question_number": 1,
          "question_text": "Describe what your Business idea is and What change your brand wants to make in people’s lives"
        },
        {
          "question_number": 2,
          "question_text": "What is your vision? (If your brand could achieve everything it wanted in the next 10 years, what would the world look like?)"
        },
        {
          "question_number": 3,
          "question_text": "What is your mission? (How do you work towards your purpose every day?)"
        },
        {
          "question_number": 4,
          "question_text": "What are your values? (3 words that describe the business you want to build)"
        },
        {
          "question_number": 5,
          "question_text": "Who is your audience persona? (Describe your ideal customer)"
        },
        {
          "question_number": 6,
          "question_text": "Who are your competitors? (List them and what they do well or poorly)"
        },
        {
          "question_number": 7,
          "question_text": "How are you different? (Why would a customer choose you over a competitor?)"
        }
      ]
    },
    {
      "section_number": 2,
      "section_title": "brand_communication",
      "questions": [
        {
          "question_number": 1,
          "question_text": "Suggest a brand name for your brand and why you choose that name?"
        },
        {
          "question_number": 2,
          "question_text": "What is the desired tone/vibe? (The feeling customers should have when they see your brand)"
        },
        {
          "question_number": 3,
          "question_text": "What is your brand voice? (How your brand would talk - e.g., serious, fun, academic)"
        },
        {
          "question_number": 4,
          "question_text": "What is your brand story? (The 'aha' moment that led to your brand's creation)"
        },
        {
          "question_number": 5,
          "question_text": "What is your hook? (The boldest promise you can make to your customers)"
        },
        {
          "question_number": 6,
          "question_text": "What is your tagline? (A one-sentence description of what your business offers)"
        }
      ]
    },
    {
      "section_number": 3,
      "section_title": "brand_identity",
      "questions": [
        {
          "question_number": 1,
          "question_text": "What is the desired mood for your visuals? (e.g., playful, trustworthy, elegant)"
        },
        {
          "question_number": 2,
          "question_text": "How do you want people to feel when they see your visuals(logo, colours etc)"
        },
        {
          "question_number": 3,
          "question_text": "Are there any colors or visuals you already associate with your brand?"
        },
        {
          "question_number": 4,
          "question_text": "What is your preferred style? (Classic vs. Modern, Serious vs. Fun, Text-heavy vs. Image-driven)"
        }
      ]
    },
    {
      "section_number": 4,
      "section_title": "marketing_and_social_media_strategy",
      "questions": [
        {
          "question_number": 1,
          "question_text": "What is the primary call to action for your audience?"
        },
        {
          "question_number": 2,
          "question_text": "What kind of content does your audience already enjoy or share?"
        },
        {
          "question_number": 3,
          "question_text": "Which social media channels do you want to focus on?"
        },
        {
          "question_number": 4,
          "question_text": "How would you handle common objections from potential customers?"
        }
      ]
    }
  ]
}




def get_question(section_number, question_number):
    for section in form_questions["sections"]:
        if section["section_number"] == section_number:
            for question in section["questions"]:
                if question["question_number"] == question_number:
                    return question["question_text"]
    return "Question not found."
  
  
  
  
def get_previous_questions(limit_section_number, limit_question_number):
    collected = []

    for section in form_questions["sections"]:
        sec_num = section["section_number"]
        for question in section["questions"]:
            q_num = question["question_number"]

            if sec_num < limit_section_number:
                collected.append(question["question_text"])
            elif sec_num == limit_section_number and q_num < limit_question_number:
                collected.append(question["question_text"])
            elif sec_num == limit_section_number and q_num >= limit_question_number:
                break
        if sec_num == limit_section_number:
            break

    return collected

