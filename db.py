import uuid
import sqlite3









# ===================== users ===========================================

# Global list of users
users = [
    {
        "userId": "userId",
        "username": "userName",
        "email": "email",
        "password": "password",
    }
]


# SQLite setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userId TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')
conn.commit()




# Create: Add a new user
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
    cursor.execute("INSERT INTO users (userId, username, email, password) VALUES (?, ?, ?, ?)",
                   (user_id, username, email, password))
    conn.commit()
    print(f"User {user_id} added.")
    return new_user




# Read: Retrieve a user by userId
def get_user(user_id):
    for user in users:
        if user["userId"] == user_id:
            return user
    cursor.execute("SELECT * FROM users WHERE userId = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return dict(zip(["userId", "username", "email", "password"], row))
    print(f"User {user_id} not found.")
    return None




# Read: Retrieve a user by email
def get_user_from_email(email):
    for user in users:
        if user["email"] == email:
            return user
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        return dict(zip(["userId", "username", "email", "password"], row))
    print(f"User with email {email} not found.")
    return None




# Update: Modify an existing user's information
def update_user(user_id, updated_info):
    for user in users:
        if user["userId"] == user_id:
            user.update(updated_info)
            for key in ["username", "email", "password"]:
                if key in updated_info:
                    cursor.execute(f"UPDATE users SET {key} = ? WHERE userId = ?", (updated_info[key], user_id))
            conn.commit()
            print(f"User {user_id} updated.")
            return "Done"
    print(f"User {user_id} not found.")




# Delete: Remove a user by userId
def delete_user(user_id):
    for i, user in enumerate(users):
        if user["userId"] == user_id:
            del users[i]
            cursor.execute("DELETE FROM users WHERE userId = ?", (user_id,))
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
        id TEXT PRIMARY KEY,
        userId TEXT NOT NULL,
        answerId TEXT,
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



# CREATE: Create an empty brand for a user
def create_brand(user_id):
    brand_id = str(uuid.uuid4())
    answers = create_answers(user_id)
    new_brand = {
        "id": brand_id,
        "userId": user_id,
        "answerId": answers["answerId"],  # Default value as in the original code
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_brand["id"], new_brand["userId"], new_brand["answerId"], new_brand["name"],
            new_brand["logo"], new_brand["brand_strategy"], new_brand["brand_communication"],
            new_brand["brand_identity"], new_brand["marketing_and_social_media_strategy"]
        ))
        conn.commit()
        print(f"Brand {brand_id} created for user {user_id}.")
        return new_brand
    except sqlite3.IntegrityError as e:
        print(f"Error creating brand: {e}")
        conn.rollback() # Rollback the transaction on error
        return None



# READ: Get a brand by ID (previously get_brands)
def get_brand(brand_id):
    cursor.execute("SELECT * FROM brands WHERE id = ?", (brand_id,))
    row = cursor.fetchone()
    if not row:
        return None
    # Dynamically create dictionary from column names and row values
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row))



# READ: Get all brands for a specific user
def get_all_user_brands(user_id):
    cursor.execute("SELECT * FROM brands WHERE userId = ?", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in rows]



# UPDATE: Update an existing brand by ID
def update_brand(brand_id, property_name, new_value):
    # Whitelist of updatable columns to prevent SQL injection on column names
    allowed_properties = [
        "name", "logo", "answerId", "brand_strategy", "brand_communication",
        "brand_identity", "marketing_and_social_media_strategy"
    ]
    if property_name not in allowed_properties:
        raise ValueError(f"Invalid or non-updatable property: {property_name}")

    # Safely construct the SQL query
    query = f"UPDATE brands SET {property_name} = ? WHERE id = ?"
    cursor.execute(query, (new_value, brand_id))
    conn.commit()

    if cursor.rowcount == 0:
        print(f"Brand {brand_id} not found or value was not changed.")
        return None
    
    print(f"Brand {brand_id} property '{property_name}' updated.")
    # Return the fully updated brand object
    return get_brand(brand_id)



# DELETE: Remove a brand by ID
def delete_brand(brand_id):
    cursor.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
    conn.commit()
    # cursor.rowcount will be 1 if a row was deleted, 0 otherwise
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
            {
            "answer_number": 1,
            "answer_text": ""
            },
            {
            "answer_number": 2,
            "answer_text": ""
            },
            {
            "answer_number": 3,
            "answer_text": ""
            },
            {
            "answer_number": 4,
            "answer_text": ""
            },
            {
            "answer_number": 5,
            "answer_text": ""
            },
            {
            "answer_number": 6,
            "answer_text": ""
            },
            {
            "answer_number": 7,
            "answer_text": ""
            }
        ]
        },
        {
        "section_number": 2,
        "section_title": "brand_communication",
        "questions": [
            {
            "answer_number": 1,
            "answer_text": ""
            },
            {
            "answer_number": 2,
            "answer_text": ""
            },
            {
            "answer_number": 3,
            "answer_text": ""
            },
            {
            "answer_number": 4,
            "answer_text": ""
            },
            {
            "answer_number": 5,
            "answer_text": ""
            },
            {
            "answer_number": 6,
            "answer_text": ""
            }
        ]
        },
        {
        "section_number": 3,
        "section_title": "brand_identity",
        "questions": [
            {
            "answer_number": 1,
            "answer_text": ""
            },
            {
            "answer_number": 2,
            "answer_text": ""
            },
            {
            "answer_number": 3,
            "answer_text": ""
            },
            {
            "answer_number": 4,
            "answer_text": ""
            }
        ]
        },
        {
        "section_number": 4,
        "section_title": "marketing_and_social_media_strategy",
        "questions": [
            {
            "answer_number": 1,
            "answer_text": ""
            },
            {
            "answer_number": 2,
            "answer_text": ""
            },
            {
            "answer_number": 3,
            "answer_text": ""
            },
            {
            "answer_number": 4,
            "answer_text": ""
            }
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
        {"answer_number": 6, "answer_text": ""},
        {"answer_number": 7, "answer_text": ""},
    ]
    },
    {
    "section_number": 2,
    "section_title": "brand_communication",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
        {"answer_number": 3, "answer_text": ""},
        {"answer_number": 4, "answer_text": ""},
        {"answer_number": 5, "answer_text": ""},
        {"answer_number": 6, "answer_text": ""},
    ]
    },
    {
    "section_number": 3,
    "section_title": "brand_identity",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
        {"answer_number": 3, "answer_text": ""},
        {"answer_number": 4, "answer_text": ""},
    ]
    },
    {
    "section_number": 4,
    "section_title": "marketing_and_social_media_strategy",
    "questions": [
        {"answer_number": 1, "answer_text": ""},
        {"answer_number": 2, "answer_text": ""},
        {"answer_number": 3, "answer_text": ""},
        {"answer_number": 4, "answer_text": ""},
    ]
}]


# Setup for answers tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_main (
        answerId TEXT PRIMARY KEY,
        userId TEXT NOT NULL,
        FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_sections (
        sectionId INTEGER PRIMARY KEY AUTOINCREMENT,
        answerId_fk TEXT NOT NULL,
        section_number INTEGER NOT NULL,
        section_title TEXT NOT NULL,
        FOREIGN KEY (answerId_fk) REFERENCES answers_main(answerId) ON DELETE CASCADE,
        UNIQUE (answerId_fk, section_number)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers_questions (
        questionId INTEGER PRIMARY KEY AUTOINCREMENT,
        sectionId_fk INTEGER NOT NULL,
        answer_number INTEGER NOT NULL,
        answer_text TEXT,
        FOREIGN KEY (sectionId_fk) REFERENCES answers_sections(sectionId) ON DELETE CASCADE,
        UNIQUE (sectionId_fk, answer_number)
    )
''')
conn.commit()


def create_answers(user_id):
    """Creates a new, empty answer object in the database for a given user."""
    answer_id = str(uuid.uuid4())
    try:
        # Start a transaction
        cursor.execute("INSERT INTO answers_main (answerId, userId) VALUES (?, ?)", (answer_id, user_id))
        
        for section_data in answers_template:
            cursor.execute("""
                INSERT INTO answers_sections (answerId_fk, section_number, section_title) 
                VALUES (?, ?, ?)
            """, (answer_id, section_data['section_number'], section_data['section_title']))
            
            section_id = cursor.lastrowid # Get the ID of the section we just inserted

            for question_data in section_data['questions']:
                cursor.execute("""
                    INSERT INTO answers_questions (sectionId_fk, answer_number, answer_text)
                    VALUES (?, ?, ?)
                """, (section_id, question_data['answer_number'], question_data['answer_text']))

        conn.commit()
        print(f"Answer object {answer_id} created for user {user_id}.")
        # Return the fully formed object by fetching it from the DB
        return get_answer(answer_id)
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during answer creation: {e}")
        return None



def get_answer(answer_id):
    """
    Retrieves a fully constructed answer object from the database by its ID.
    This function reconstructs the nested dictionary structure from the normalized tables.
    """
    # First, verify the main answer object exists
    cursor.execute("SELECT userId FROM answers_main WHERE answerId = ?", (answer_id,))
    main_row = cursor.fetchone()
    if not main_row:
        return None

    result = {"answerId": answer_id, "userId": main_row[0], "sections": []}
    
    # Get all sections for this answerId
    cursor.execute("""
        SELECT sectionId, section_number, section_title 
        FROM answers_sections 
        WHERE answerId_fk = ? 
        ORDER BY section_number
    """, (answer_id,))
    sections = cursor.fetchall()
    
    for sec_id, sec_num, sec_title in sections:
        section_obj = {
            "section_number": sec_num,
            "section_title": sec_title,
            "questions": []
        }
        
        # Get all questions for this section
        cursor.execute("""
            SELECT answer_number, answer_text 
            FROM answers_questions 
            WHERE sectionId_fk = ? 
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



def get_answer_from_number(answer_id, section_number, answer_number):
    """Returns the text of a specific answer from a specific section."""
    cursor.execute("""
        SELECT aq.answer_text 
        FROM answers_questions AS aq
        JOIN answers_sections AS asec ON aq.sectionId_fk = asec.sectionId
        WHERE asec.answerId_fk = ? AND asec.section_number = ? AND aq.answer_number = ?
    """, (answer_id, section_number, answer_number))
    
    row = cursor.fetchone()
    return row[0] if row else None



def get_previous_answers(answer_id, limit_section_number, limit_answer_number):
    """
    Returns a list of all previous answers, from section 1, answer 1,
    up to, but not including, the specified answer.
    """
    cursor.execute("""
        SELECT aq.answer_text
        FROM answers_questions AS aq
        JOIN answers_sections AS asec ON aq.sectionId_fk = asec.sectionId
        WHERE asec.answerId_fk = ?
          AND (
            asec.section_number < ?
            OR (asec.section_number = ? AND aq.answer_number < ?)
          )
        ORDER BY asec.section_number, aq.answer_number;
    """, (answer_id, limit_section_number, limit_section_number, limit_answer_number))
    
    # Fetch all rows and flatten the list of tuples into a list of strings
    rows = cursor.fetchall()
    return [row[0] for row in rows]



def update_answer(answer_id, section_number, answer_number, new_text):
    """Updates the text of a specific answer in a specific section."""
    try:
        cursor.execute("""
            UPDATE answers_questions
            SET answer_text = ?
            WHERE answer_number = ? AND sectionId_fk = (
                SELECT sectionId FROM answers_sections
                WHERE answerId_fk = ? AND section_number = ?
            )
        """, (new_text, answer_number, answer_id, section_number))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Answer updated successfully for {answer_id}.")
            return True
        else:
            print(f"No answer found to update for answerId {answer_id}, section {section_number}, answer {answer_number}.")
            return False
    except sqlite3.Error as e:
        print(f"Database error during answer update: {e}")
        return False



def delete_answer(answer_id):
    """
    Deletes an entire answer object and all its associated sections and questions
    from the database using its ID. The `ON DELETE CASCADE` pragma handles the cleanup.
    """
    cursor.execute("DELETE FROM answers_main WHERE answerId = ?", (answer_id,))
    conn.commit()
    
    if cursor.rowcount > 0:
        print(f"Answer object {answer_id} deleted successfully.")
        return True
    else:
        print(f"Answer object {answer_id} not found.")
        return False
    
    
# print(create_brand("userId"))
# if __name__ == "__main__":
    # 1. Create a fresh user
    # user = create_user("testuser", "test@example.com", "secret")
    # if not user:
    #     print("🔴 Failed to create user—maybe the email already exists?")
    #     exit(1)
    # print("✅ Created user:", user)

    # # 2. Create a brand for that user
    # brand = create_brand("e19d521a-38b2-4f97-9d7c-b18da76b4ee8")
    # if not brand:
    #     # print("🔴 Failed to create brand for user", user["userId"])
    #     exit(1)
    # print("✅ Created brand:", brand)

    # # 3. Fetch all brands for that user
    # brands = get_all_user_brands("e19d521a-38b2-4f97-9d7c-b18da76b4ee8")
    # print("🔎 get_all_user_brands returned:", brands)

    # 4. Simple assertion
    # assert len(brands) == 1 and brands[0]["id"] == brand["id"], \
    #     "❌ Expected exactly one brand matching the one we just created!"
    # print("🎉 Test passed!")