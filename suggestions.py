import questions
import db
import openAI



system_message = 'You are a suggestion AI. You generate very relevant suggestions for users. You do not say any other thing. All you say is the suggestion. Make sure to output all suggestions as a pythin list of strings of the format ["suggestion1", "suggestion2", .... "suggestionN"]. Make sure to follow the format. Make sure your suggestiosn are things the user would want to say. Make sure to be as detailed as needed, but dont add unnecessary details to the answer. Make sure to capture the users speaking style, Make sure the suggestions are very relevant to the question asked. Make sure all suggestions are unique and not repeated or linked.'


def get_suggestions(question_number, answerId, number_of_suggestions):
    print(f"get_suggestions function debug:")
    print(f"  question_number: {question_number}")
    print(f"  answerId: {answerId}")
    print(f"  number_of_suggestions: {number_of_suggestions}")
    
    question = questions.get_question(question_number)
    print(f"  current question: {question}")
    
    previous_questions = questions.get_previous_questions(question_number)
    print(f"  previous_questions count: {len(previous_questions)}")
    print(f"  previous_questions: {previous_questions}")
    
    previous_answers = db.get_previous_answers(answerId, question_number)
    print(f"  previous_answers count: {len(previous_answers)}")
    print(f"  previous_answers: {previous_answers}")
    
    # Check if we have matching counts
    if len(previous_questions) != len(previous_answers):
        print(f"  WARNING: Mismatch! {len(previous_questions)} questions vs {len(previous_answers)} answers")
    
    question_and_answers = " ".join([f"Question: {q} Answer: {a}." for q, a in zip(previous_questions, previous_answers)])
    print(f"  question_and_answers length: {len(question_and_answers)}")
    print(f"  question_and_answers preview: {question_and_answers[:200]}...")
    
    prompt = "Here's a list of the previous questions and answers: " + question_and_answers + ". Now, based on the question: " + question + ", generate "+str(number_of_suggestions)+" straight forward suggestions."
    print(f"  prompt length: {len(prompt)}")
    
    try:
        suggestions = openAI.get_text_prediction(system_message, prompt)
        print(f"  openAI response: {suggestions}")
        return suggestions
    except Exception as e:
        print(f"  Error calling openAI: {e}")
        return {'error': f'OpenAI API error: {str(e)}'}


def generate_suggestions(question_number, answerId):
    print(f"suggestions.generate_suggestions debug:")
    print(f"  question_number: {question_number}")
    print(f"  answerId: {answerId}")
    print(f"  questions length: {len(questions.questions)}")
    
    if 1 <= question_number <= len(questions.questions):
        try:
            result = get_suggestions(question_number, answerId, 2)
            print(f"  get_suggestions result: {result}")
            return result
        except Exception as e:
            print(f"  Error in get_suggestions: {e}")
            return {'error': f'Suggestions generation failed: {str(e)}'}
    else:
        error_msg = f'Invalid question_number: {question_number}.'
        print(f"  {error_msg}")
        return {'error': error_msg}
        
        
        
# print(generate_suggestions(1, 2, 'userId')["suggestions"])
# print(generate_suggestions(1, 2, 'de104597-9497-42f3-9142-761b7c22d7c6'))
