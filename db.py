# db.py - now uses Neon Postgres (psycopg2) and loads connection string from .env
import os
from dotenv import load_dotenv
import uuid
import psycopg2
import psycopg2.extras

load_dotenv()  # Load environment variables from .env

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def reset_connection():
    """Reset the database connection if it's in a failed state"""
    global conn, cursor
    try:
        conn.rollback()
    except:
        pass
    try:
        conn.close()
    except:
        pass
    
    # Reconnect
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def test_connection():
    """Test if the database connection is working"""
    try:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("Database connection test: SUCCESS")
        return True
    except Exception as e:
        print(f"Database connection test: FAILED - {e}")
        return False

# Test the connection on startup
test_connection()

# ===================== users ===========================================

users = [
    {
        "userId": "userId",
        "username": "userName",
        "email": "email",
        "password": "password",
    }
]

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userId UUID PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')
conn.commit()

def create_user(username, email, password):
    if any(user['email'] == email for user in users):
        print(f"User with email {email} already exists.")
        return
    user_id = str(uuid.uuid4())
    new_user = {
        "userId": user_id,
        "username": username,
        "email": email,
        "password": password,
    }
    users.append(new_user)
    cursor.execute("INSERT INTO users (userId, username, email, password) VALUES (%s, %s, %s, %s)",
                   (user_id, username, email, password))
    conn.commit()
    print(f"User {user_id} added.")
    return new_user

def get_user(user_id):
    for user in users:
        if user["userId"] == user_id:
            return user
    
    # Try up to 2 times with connection reset
    for attempt in range(2):
        try:
            cursor.execute("SELECT * FROM users WHERE userId = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            print(f"User {user_id} not found.")
            return None
        except psycopg2.Error as e:
            print(f"Database error in get_user (attempt {attempt + 1}): {e}")
            if attempt == 0:  # Only reset on first failure
                reset_connection()
            else:
                return None
    
    return None

def get_user_from_email(email):
    for user in users:
        if user["email"] == email:
            return user
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    print(f"User with email {email} not found.")
    return None

def update_user(user_id, updated_info):
    for user in users:
        if user["userId"] == user_id:
            user.update(updated_info)
            for key in ["username", "email", "password"]:
                if key in updated_info:
                    cursor.execute(f"UPDATE users SET {key} = %s WHERE userId = %s", (updated_info[key], user_id))
            conn.commit()
            print(f"User {user_id} updated.")
            return "Done"
    print(f"User {user_id} not found.")

def delete_user(user_id):
    for i, user in enumerate(users):
        if user["userId"] == user_id:
            del users[i]
            cursor.execute("DELETE FROM users WHERE userId = %s", (user_id,))
            conn.commit()
            print(f"User {user_id} deleted.")
            return "Done"
    print(f"User {user_id} not found.")

# ===================== Brands ===========================================

brands = [{
    "id": "brandId",
    "userId": "userId",
    "answerId": "answerId",
    "name": "Brand name",
    "logo": "Brand logo",
    "brand_strategy": "brand_strategy_id",
    "brand_communication": "brand_communication_id",
    "brand_identity": "brand_identity_id",
    "marketing_and_social_media_strategy": "marketing_and_social_media_strategy_id",
}]

cursor.execute('''
    CREATE TABLE IF NOT EXISTS brands (
        id UUID PRIMARY KEY,
        userId UUID NOT NULL,
        answerId UUID,
        name TEXT,
        logo TEXT,
        brand_strategy TEXT,
        brand_communication TEXT,
        brand_identity TEXT,
        marketing_and_social_media_strategy TEXT,
        FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
    )
''')
conn.commit()

def create_brand(user_id):
    brand_id = str(uuid.uuid4())
    answers = create_answers(user_id)
    
    # Debug: Print the answers object
    print("Answers object:", answers)
    
    if not answers:
        print(f"Failed to create answers for user {user_id}")
        return None
    
    new_brand = {
        "id": brand_id,
        "userId": user_id,
        "answerId": answers["answerId"],
        "name": "",
        "logo": "",
        "brand_strategy": "",
        "brand_communication": "",
        "brand_identity": "",
        "marketing_and_social_media_strategy": "",
    }
    try:
        cursor.execute("""
            INSERT INTO brands (id, userId, answerId, name, logo, brand_strategy, brand_communication, brand_identity, marketing_and_social_media_strategy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            new_brand["id"], new_brand["userId"], new_brand["answerId"], new_brand["name"],
            new_brand["logo"], new_brand["brand_strategy"], new_brand["brand_communication"],
            new_brand["brand_identity"], new_brand["marketing_and_social_media_strategy"]
        ))
        conn.commit()
        print(f"Brand {brand_id} created for user {user_id}.")
        return new_brand
    except psycopg2.IntegrityError as e:
        print(f"Error creating brand: {e}")
        conn.rollback()
        return None

def get_brand(brand_id):
    # Try up to 2 times with connection reset
    for attempt in range(2):
        try:
            cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
        except psycopg2.Error as e:
            print(f"Database error in get_brand (attempt {attempt + 1}): {e}")
            if attempt == 0:  # Only reset on first failure
                reset_connection()
            else:
                return None
    
    return None

def get_all_user_brands(user_id):
    cursor.execute("SELECT * FROM brands WHERE userId = %s", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        return []
    return [dict(row) for row in rows]

def update_brand(brand_id, property_name, new_value):
    allowed_properties = [
        "name", "logo", "answerId", "brand_strategy", "brand_communication",
        "brand_identity", "marketing_and_social_media_strategy"
    ]
    if property_name not in allowed_properties:
        raise ValueError(f"Invalid or non-updatable property: {property_name}")
    query = f"UPDATE brands SET {property_name} = %s WHERE id = %s"
    cursor.execute(query, (new_value, brand_id))
    conn.commit()
    if cursor.rowcount == 0:
        print(f"Brand {brand_id} not found or value was not changed.")
        return None
    print(f"Brand {brand_id} property '{property_name}' updated.")
    return get_brand(brand_id)

def delete_brand(brand_id):
    cursor.execute("DELETE FROM brands WHERE id = %s", (brand_id,))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"Brand {brand_id} has been deleted.")
        return True
    else:
        print(f"Brand {brand_id} not found.")
        return False

# ===================== answers ===========================================

answers = [{
    "answerId": "answerId",
    "userId": "userId",
    "sections": [
        {
        "section_number": 1,
        "section_title": "brand_strategy",
        "questions": [
            {"answer_number": 1, "answer_text": ""},
            {"answer_number": 2, "answer_text": ""},
            {"answer_number": 3, "answer_text": ""},
            {"answer_number": 4, "answer_text": ""},
            {"answer_number": 5, "answer_text": ""},
           
            
        ]
        },
        {
        "section_number": 2,
        "section_title": "brand_communication",
        "questions": [
            {"answer_number": 1, "answer_text": ""},
            {"answer_number": 2, "answer_text": ""},
          
        ]
        },
        {
        "section_number": 3,
        "section_title": "brand_identity",
        "questions": [
            {"answer_number": 1, "answer_text": ""},
           
        ]
        },
        {
        "section_number": 4,
        "section_title": "marketing_and_social_media_strategy",
        "questions": [
            {"answer_number": 1, "answer_text": ""},
            {"answer_number": 2, "answer_text": ""},
         
        ]
    }
    ]
}]

answers_template = [
    {
    "section_number": 1,
    "section_title": "brand_strategy",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
        {"answer_number": 3, "answer_text": ""},
        {"answer_number": 4, "answer_text": ""},
        {"answer_number": 5, "answer_text": ""},
       
    ]
    },
    {
    "section_number": 2,
    "section_title": "brand_communication",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
        
    ]
    },
    {
    "section_number": 3,
    "section_title": "brand_identity",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
       
    ]
    },
    {
    "section_number": 4,
    "section_title": "marketing_and_social_media_strategy",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
      
    ]
}]

cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_main (
        answerId UUID PRIMARY KEY,
        userId UUID NOT NULL,
        FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_sections (
        sectionId SERIAL PRIMARY KEY,
        answerId_fk UUID NOT NULL,
        section_number INT NOT NULL,
        section_title TEXT NOT NULL,
        FOREIGN KEY (answerId_fk) REFERENCES answers_main(answerId) ON DELETE CASCADE,
        UNIQUE (answerId_fk, section_number)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_questions (
        questionId SERIAL PRIMARY KEY,
        sectionId_fk INT NOT NULL,
        answer_number INT NOT NULL,
        global_question_number INT NOT NULL,
        answer_text TEXT,
        FOREIGN KEY (sectionId_fk) REFERENCES answers_sections(sectionId) ON DELETE CASCADE,
        UNIQUE (sectionId_fk, answer_number),
        UNIQUE (sectionId_fk, global_question_number)
    )
''')

# Table to store Cloudinary image URLs
cursor.execute('''
    CREATE TABLE IF NOT EXISTS answer_images (
        imageId SERIAL PRIMARY KEY,
        answerId_fk UUID NOT NULL,
        section_number INT NOT NULL,
        question_number INT NOT NULL,
        cloudinary_url TEXT NOT NULL,
        cloudinary_public_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (answerId_fk) REFERENCES answers_main(answerId) ON DELETE CASCADE,
        UNIQUE (answerId_fk, section_number, question_number)
    )
''')
conn.commit()

# Helper: Map (section_number, answer_number) to global_question_number
from questions import questions as flat_questions

def get_global_question_number(section_number, answer_number):
    # You may want to keep a mapping for this, but for now, assume flat order
    # section 1: 1-5, section 2: 6-7, section 3: 8, section 4: 9-10
    section_map = {
        1: 0,  # section 1 starts at index 0
        2: 5,  # section 2 starts at index 5
        3: 7,  # section 3 starts at index 7
        4: 8   # section 4 starts at index 8
    }
    return section_map[section_number] + answer_number

def get_section_and_answer_number(global_question_number):
    # Reverse mapping for 10 questions, adjust if you add more
    if 1 <= global_question_number <= 5:
        return 1, global_question_number
    elif 6 <= global_question_number <= 7:
        return 2, global_question_number - 5
    elif global_question_number == 8:
        return 3, 1
    elif 9 <= global_question_number <= 10:
        return 4, global_question_number - 8
    else:
        raise ValueError('Invalid global_question_number')

def create_answers(user_id):
    answer_id = str(uuid.uuid4())
    try:
        cursor.execute("INSERT INTO answers_main (answerId, userId) VALUES (%s, %s)", (answer_id, user_id))
        global_qn = 1
        for section_data in answers_template:
            cursor.execute(
                "INSERT INTO answers_sections (answerId_fk, section_number, section_title) VALUES (%s, %s, %s) RETURNING sectionId",
                (answer_id, section_data['section_number'], section_data['section_title'])
            )
            section_id = cursor.fetchone()[0]
            for question_data in section_data['questions']:
                cursor.execute(
                    "INSERT INTO answers_questions (sectionId_fk, answer_number, global_question_number, answer_text) VALUES (%s, %s, %s, %s)",
                    (section_id, question_data['answer_number'], global_qn, question_data['answer_text'])
                )
                global_qn += 1
        conn.commit()
        print(f"Answer object {answer_id} created for user {user_id}.")
        return get_answer(answer_id)
    except psycopg2.InterfaceError as e:
        print(f"[create_answers] InterfaceError: {e}. Resetting connection and retrying once.")
        reset_connection()
        try:
            cursor.execute("INSERT INTO answers_main (answerId, userId) VALUES (%s, %s)", (answer_id, user_id))
            global_qn = 1
            for section_data in answers_template:
                cursor.execute(
                    "INSERT INTO answers_sections (answerId_fk, section_number, section_title) VALUES (%s, %s, %s) RETURNING sectionId",
                    (answer_id, section_data['section_number'], section_data['section_title'])
                )
                section_id = cursor.fetchone()[0]
                for question_data in section_data['questions']:
                    cursor.execute(
                        "INSERT INTO answers_questions (sectionId_fk, answer_number, global_question_number, answer_text) VALUES (%s, %s, %s, %s)",
                        (section_id, question_data['answer_number'], global_qn, question_data['answer_text'])
                    )
                    global_qn += 1
            conn.commit()
            print(f"Answer object {answer_id} created for user {user_id} (after reset).")
            return get_answer(answer_id)
        except Exception as e2:
            conn.rollback()
            print(f"Database error during answer creation after reset: {e2}")
            return None
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error during answer creation: {e.pgerror}")
        return None

def get_answer(answer_id):
    for attempt in range(2):
        try:
            cursor.execute("SELECT userId FROM answers_main WHERE answerId = %s", (answer_id,))
            main_row = cursor.fetchone()
            if not main_row:
                return None
            result = {"answerId": answer_id, "userId": main_row[0], "sections": []}
            cursor.execute("""
                SELECT sectionId, section_number, section_title 
                FROM answers_sections 
                WHERE answerId_fk = %s 
                ORDER BY section_number
            """, (answer_id,))
            sections = cursor.fetchall()
            for sec_id, sec_num, sec_title in sections:
                section_obj = {
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "questions": []
                }
                cursor.execute("""
                    SELECT answer_number, answer_text 
                    FROM answers_questions 
                    WHERE sectionId_fk = %s 
                    ORDER BY answer_number
                """, (sec_id,))
                questions = cursor.fetchall()
                for ans_num, ans_text in questions:
                    section_obj["questions"].append({
                        "answer_number": ans_num,
                        "answer_text": ans_text
                    })
                result["sections"].append(section_obj)
            return result
        except psycopg2.InterfaceError as e:
            print(f"[get_answer] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_answer: {e}")
            reset_connection()
            return None
    return None

def get_answer_from_number(answer_id, section_number, answer_number):
    for attempt in range(2):
        try:
            cursor.execute("""
                SELECT aq.answer_text 
                FROM answers_questions AS aq
                JOIN answers_sections AS asec ON aq.sectionId_fk = asec.sectionId
                WHERE asec.answerId_fk = %s AND asec.section_number = %s AND aq.answer_number = %s
            """, (answer_id, section_number, answer_number))
            row = cursor.fetchone()
            return row[0] if row else None
        except psycopg2.InterfaceError as e:
            print(f"[get_answer_from_number] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_answer_from_number: {e}")
            reset_connection()
            return None
    return None

def get_previous_answers(answer_id, limit_global_question_number):
    print(f"get_previous_answers debug:")
    print(f"  answer_id: {answer_id}")
    print(f"  limit_global_question_number: {limit_global_question_number}")
    query = """
        SELECT aq.answer_text
        FROM answers_questions AS aq
        JOIN answers_sections AS asec ON aq.sectionId_fk = asec.sectionId
        WHERE asec.answerId_fk = %s AND aq.global_question_number < %s
        ORDER BY aq.global_question_number;
    """
    print(f"  SQL query: {query}")
    print(f"  SQL params: ({answer_id}, {limit_global_question_number})")
    try:
        cursor.execute(query, (answer_id, limit_global_question_number))
        rows = cursor.fetchall()
        print(f"  SQL result rows: {rows}")
        result = [row[0] for row in rows]
        print(f"  Final result: {result}")
        return result
    except psycopg2.InterfaceError as e:
        print(f"[get_previous_answers] InterfaceError: {e}. Resetting connection and retrying once.")
        reset_connection()
        try:
            cursor.execute(query, (answer_id, limit_global_question_number))
            rows = cursor.fetchall()
            print(f"  SQL result rows (after reset): {rows}")
            result = [row[0] for row in rows]
            print(f"  Final result (after reset): {result}")
            return result
        except Exception as e2:
            print(f"  Database error in get_previous_answers after reset: {e2}")
            return []
    except psycopg2.Error as e:
        print(f"  Database error in get_previous_answers: {e}")
        reset_connection()
        return []

def update_answer(answer_id, global_question_number, new_text):
    try:
        print(f"[update_answer] Attempting update: answer_id={answer_id}, global_question_number={global_question_number}, new_text={new_text}")
        cursor.execute("""
            UPDATE answers_questions
            SET answer_text = %s
            WHERE global_question_number = %s AND sectionId_fk IN (
                SELECT sectionId FROM answers_sections WHERE answerId_fk = %s
            )
        """, (new_text, global_question_number, answer_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"[update_answer] Answer updated successfully for answer_id={answer_id}, global_question_number={global_question_number}.")
            return True
        else:
            print(f"[update_answer] No answer found to update for answer_id={answer_id}, global_question_number={global_question_number}. Attempting upsert...")
            section_number, answer_number = get_section_and_answer_number(global_question_number)
            cursor.execute("SELECT sectionId FROM answers_sections WHERE answerId_fk = %s AND section_number = %s", (answer_id, section_number))
            section_row = cursor.fetchone()
            if not section_row:
                print(f"[update_answer] No section found for answer_id={answer_id}, section_number={section_number}. Cannot upsert.")
                return {'error': f'No section found for answer_id={answer_id}, section_number={section_number}. Cannot upsert.'}
            section_id = section_row[0]
            try:
                cursor.execute("""
                    INSERT INTO answers_questions (sectionId_fk, answer_number, global_question_number, answer_text)
                    VALUES (%s, %s, %s, %s)
                """, (section_id, answer_number, global_question_number, new_text))
                conn.commit()
                print(f"[update_answer] Inserted new answer for answer_id={answer_id}, global_question_number={global_question_number}.")
                return True
            except psycopg2.Error as e:
                print(f"[update_answer] Database error during upsert: {e}")
                conn.rollback()
                return {'error': f'Database error during upsert: {e}'}
    except psycopg2.InterfaceError as e:
        print(f"[update_answer] InterfaceError: {e}. Resetting connection and retrying once.")
        reset_connection()
        try:
            cursor.execute("""
                UPDATE answers_questions
                SET answer_text = %s
                WHERE global_question_number = %s AND sectionId_fk IN (
                    SELECT sectionId FROM answers_sections WHERE answerId_fk = %s
                )
            """, (new_text, global_question_number, answer_id))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"[update_answer] Answer updated successfully for answer_id={answer_id}, global_question_number={global_question_number} (after reset).")
                return True
            else:
                print(f"[update_answer] No answer found to update for answer_id={answer_id}, global_question_number={global_question_number} (after reset). Attempting upsert...")
                section_number, answer_number = get_section_and_answer_number(global_question_number)
                cursor.execute("SELECT sectionId FROM answers_sections WHERE answerId_fk = %s AND section_number = %s", (answer_id, section_number))
                section_row = cursor.fetchone()
                if not section_row:
                    print(f"[update_answer] No section found for answer_id={answer_id}, section_number={section_number} (after reset). Cannot upsert.")
                    return {'error': f'No section found for answer_id={answer_id}, section_number={section_number} (after reset). Cannot upsert.'}
                section_id = section_row[0]
                try:
                    cursor.execute("""
                        INSERT INTO answers_questions (sectionId_fk, answer_number, global_question_number, answer_text)
                        VALUES (%s, %s, %s, %s)
                    """, (section_id, answer_number, global_question_number, new_text))
                    conn.commit()
                    print(f"[update_answer] Inserted new answer for answer_id={answer_id}, global_question_number={global_question_number} (after reset).")
                    return True
                except psycopg2.Error as e2:
                    print(f"[update_answer] Database error during upsert after reset: {e2}")
                    conn.rollback()
                    return {'error': f'Database error during upsert after reset: {e2}'}
        except Exception as e2:
            conn.rollback()
            print(f"[update_answer] Database error during answer update after reset: {e2}")
            return {'error': f'Database error during answer update after reset: {e2}'}
    except psycopg2.Error as e:
        print(f"[update_answer] Database error during answer update: {e}")
        conn.rollback()
        return {'error': f'Database error during answer update: {e}'}

def delete_answer(answer_id):
    for attempt in range(2):
        try:
            cursor.execute("DELETE FROM answers_main WHERE answerId = %s", (answer_id,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Answer object {answer_id} deleted successfully.")
                return True
            else:
                print(f"Answer object {answer_id} not found.")
                return False
        except psycopg2.InterfaceError as e:
            print(f"[delete_answer] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in delete_answer: {e}")
            conn.rollback()
            return False
    return False

# ===================== Cloudinary Image Management ===========================================

def save_image_url(answer_id, section_number, question_number, cloudinary_url, cloudinary_public_id):
    for attempt in range(2):
        try:
            cursor.execute("""
                INSERT INTO answer_images (answerId_fk, section_number, question_number, cloudinary_url, cloudinary_public_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (answerId_fk, section_number, question_number)
                DO UPDATE SET 
                    cloudinary_url = EXCLUDED.cloudinary_url,
                    cloudinary_public_id = EXCLUDED.cloudinary_public_id,
                    created_at = CURRENT_TIMESTAMP
            """, (answer_id, section_number, question_number, cloudinary_url, cloudinary_public_id))
            conn.commit()
            print(f"Image URL saved for answer {answer_id}, section {section_number}, question {question_number}")
            return True
        except psycopg2.InterfaceError as e:
            print(f"[save_image_url] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error saving image URL: {e}")
            conn.rollback()
            return False
    return False

def get_image_url(answer_id, section_number, question_number):
    for attempt in range(2):
        try:
            cursor.execute("""
                SELECT cloudinary_url, cloudinary_public_id, created_at
                FROM answer_images
                WHERE answerId_fk = %s AND section_number = %s AND question_number = %s
            """, (answer_id, section_number, question_number))
            row = cursor.fetchone()
            if row:
                return {
                    "cloudinary_url": row[0],
                    "cloudinary_public_id": row[1],
                    "created_at": row[2]
                }
            return None
        except psycopg2.InterfaceError as e:
            print(f"[get_image_url] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error getting image URL: {e}")
            return None
    return None

def delete_image_url(answer_id, section_number, question_number):
    for attempt in range(2):
        try:
            cursor.execute("""
                DELETE FROM answer_images
                WHERE answerId_fk = %s AND section_number = %s AND question_number = %s
            """, (answer_id, section_number, question_number))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"Image URL deleted for answer {answer_id}, section {section_number}, question {question_number}")
                return True
            return False
        except psycopg2.InterfaceError as e:
            print(f"[delete_image_url] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error deleting image URL: {e}")
            conn.rollback()
            return False
    return False

def get_all_images_for_answer(answer_id):
    for attempt in range(2):
        try:
            cursor.execute("""
                SELECT section_number, question_number, cloudinary_url, cloudinary_public_id, created_at
                FROM answer_images
                WHERE answerId_fk = %s
                ORDER BY section_number, question_number
            """, (answer_id,))
            rows = cursor.fetchall()
            return [
                {
                    "section_number": row[0],
                    "question_number": row[1],
                    "cloudinary_url": row[2],
                    "cloudinary_public_id": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]
        except psycopg2.InterfaceError as e:
            print(f"[get_all_images_for_answer] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error getting all images: {e}")
            return []
    return []