import questions
import db
import openAI



system_message = 'You are a suggestion AI. You generate very relevant suggestions for users. You do not say any other thing. All you say is the suggestion. Make sure to output all suggestions as a pythin list of strings of the format ["suggestion1", "suggestion2", .... "suggestionN"]. Make sure to follow the format. Make sure your suggestiosn are things the user would want to say. Make sure to be as detailed as needed, but dont add unnecessary details to the answer. Make sure to capture the users speaking style, Make sure the suggestions are very relevant to the question asked. Make sure all suggestions are unique and not repeated or linked.'


def get_suggestions(question_number, answerId, number_of_suggestions):
    question = questions.get_question(question_number)
    previous_questions = questions.get_previous_questions(question_number)
    previous_answers = db.get_previous_answers(answerId, question_number)
    question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
    suggestions = openAI.get_text_prediction(system_message, "Here's a list of the previous questions and answers: " + question_and_answers + ". Now, based on the question: " + question + ", generate "+str(number_of_suggestions)+" straight forward suggestions.")
    return suggestions


def generate_suggestions(question_number, answerId):
    if 1 <= question_number <= len(questions.questions):
        return get_suggestions(question_number, answerId, 2)
    else:
        return {'error': f'Invalid question_number: {question_number}.'}
        
        
        
# print(generate_suggestions(1, 2, 'userId')["suggestions"])
# print(generate_suggestions(1, 2, 'de104597-9497-42f3-9142-761b7c22d7c6'))
