import questions
import db
import openAI



system_message = 'You are a suggestion AI. You generate very relevant suggestions for users. You do not say any other thing. All you say is the suggestion. Make sure to output all suggestions as a pythin list of strings of the format ["suggestion1", "suggestion2", .... "suggestionN"]. Make sure to follow the format. Make sure your suggestiosn are things the user would want to say. Make sure to be as detailed as needed, but dont add unnecessary details to the answer. Make sure to capture the users speaking style, Make sure the suggestions are very relevant to the question asked. Make sure all suggestions are unique and not repeated or linked.'


def get_suggestions(section_number, question_number, answerId, number_of_suggestions):
    question = questions.get_question(section_number, question_number)
    previous_questions = questions.get_previous_questions(section_number, question_number)
    previous_answers = db.get_previous_answers(answerId, section_number, question_number)
    question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
    # print("Question and answers: "+question_and_answers)
    
    suggestions = openAI.get_text_prediction(system_message, "Here's a list of the previous questions and answers: " + question_and_answers + ". Now, based on the question: " + question + ", generate "+str(number_of_suggestions)+" straight forward suggestions.")
    
    return suggestions







def generate_suggestions(section_number, question_number, answerId):
    match section_number:
        case 1:  # brand_strategy
            match question_number:
                case 1:
                    # Logic for: "What is your purpose? (The 'why' behind what you do, beyond making a profit)"
                    pass
                case 2:
                    # Logic for: "What is your vision? (If your brand could achieve everything...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 3:
                    # Logic for: "What is your mission? (How do you work towards your purpose every day?)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 4:
                    # Logic for: "What are your values? (3 words that describe the business...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 5:
                    # Logic for: "Who is your audience persona? (Describe your ideal customer)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 6:
                    # Logic for: "Who are your competitors? (List them and what they do well or poorly)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 7:
                    # Logic for: "How are you different? (Why would a customer choose you...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case _:
                    return {'error': f'Invalid question_number number: {question_number} for section_number {section_number}.'}
        
        case 2:  # brand_communication
            match question_number:
                case 1:
                    # Logic for: "What is your brand name's personality? (If your brand was a person...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 2:
                    # Logic for: "What is the desired tone/vibe? (The feeling customers should have...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 3:
                    # Logic for: "What is your brand voice? (How your brand would talk...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 4:
                    # Logic for: "What is your brand story? (The 'aha' moment...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 5:
                    # Logic for: "What is your hook? (The boldest promise you can make...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 6:
                    # Logic for: "What is your tagline? (A one-sentence description...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case _:
                    return {'error': f'Invalid question_number number: {question_number} for section_number {section_number}.'}

        case 3:  # brand_identity
            match question_number:
                case 1:
                    # Logic for: "What is the desired mood for your visuals? (e.g., playful, trustworthy...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 2:
                    # Logic for: "How do you want your brand to feel different within your industry?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 3:
                    # Logic for: "Are there any colors or visuals you already associate with your brand?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 4:
                    # Logic for: "What is your preferred style? (Classic vs. Modern, Serious vs. Fun...)"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case _:
                    return {'error': f'Invalid question_number number: {question_number} for section_number {section_number}.'}

        case 4:  # marketing_and_social_media_strategy
            match question_number:
                case 1:
                    # Logic for: "What is the primary call to action for your audience?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 2:
                    # Logic for: "What kind of content does your audience already enjoy or share?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 3:
                    # Logic for: "Which social media channels do you want to focus on?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case 4:
                    # Logic for: "How would you handle common objections from potential customers?"
                    return get_suggestions(section_number, question_number, answerId, 2)
                case _:
                    return {'error': f'Invalid question_number number: {question_number} for section_number {section_number}.'}

        case _:
            return {'error': f'Invalid section_number number: {section_number}.'}
        
        
        
# print(generate_suggestions(1, 2, 'userId')["suggestions"])
# print(generate_suggestions(1, 2, 'de104597-9497-42f3-9142-761b7c22d7c6'))
