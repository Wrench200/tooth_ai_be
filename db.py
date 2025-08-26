# db.py - now uses Neon Postgres (psycopg2) and loads connection string from .env
import os
import json
from dotenv import load_dotenv
import uuid
import psycopg2
import psycopg2.extras
import urllib.parse
import threading
import time
from contextlib import contextmanager

load_dotenv()  # Load environment variables from .env

DATABASE_URL = os.getenv("DATABASE_URL")

def fix_database_url(url):
    """Fix common issues with DATABASE_URL format"""
    if not url:
        return url
    
    # Fix sslmode parameter if it's malformed
    if 'sslmode' in url and 'sslmode=' not in url:
        # Replace malformed sslmode with correct format
        url = url.replace('?sslmode&', '?sslmode=require&')
        url = url.replace('&sslmode&', '&sslmode=require&')
        url = url.replace('&sslmode', '&sslmode=require')
        if url.endswith('?sslmode'):
            url = url.replace('?sslmode', '?sslmode=require')
    
    # Ensure sslmode is set for production
    if 'sslmode=' not in url:
        if '?' in url:
            url += '&sslmode=require'
        else:
            url += '?sslmode=require'
    
    return url

# Fix the DATABASE_URL if needed
DATABASE_URL = fix_database_url(DATABASE_URL)

class ThreadLocalConnection:
    """Thread-local database connection manager with SSL support"""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self._thread_local = threading.local()
    
    def _create_connection(self):
        """Create a new database connection with proper SSL settings"""
        try:
            conn = psycopg2.connect(self.database_url)
            
            # Set basic session parameters
            conn.autocommit = False
            
            return conn
            
        except Exception as e:
            print(f"Error creating database connection: {e}")
            raise
    
    def _is_connection_valid(self, conn):
        """Check if a connection is still valid"""
        if conn is None:
            return False
        
        try:
            # Check if connection is still alive
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
            return False
    
    def get_connection(self):
        """Get a valid database connection for the current thread"""
        # For now, always create a new connection to avoid issues
        conn = self._create_connection()
        return conn
    
    def close_connection(self):
        """Close the current thread's database connection"""
        if hasattr(self._thread_local, 'connection'):
            try:
                self._thread_local.connection.close()
            except:
                pass
            delattr(self._thread_local, 'connection')

# Create global thread-local connection manager
db_manager = ThreadLocalConnection(DATABASE_URL)

@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic error handling"""
    conn = None
    cursor = None
    
    # First attempt
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
        return  # Success, exit early
    except psycopg2.OperationalError as e:
        print(f"Database operational error: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        # Don't yield here - this was causing the nested yield issue
    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
    
    # Second attempt (only if first attempt failed with OperationalError)
    conn = None
    cursor = None
    try:
        db_manager.close_connection()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        print(f"Database retry failed: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass

def reset_connection():
    """Reset the current thread's database connection"""
    db_manager.close_connection()

def test_connection():
    """Test if the database connection is working"""
    try:
        with get_db_connection() as cursor:
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

with get_db_connection() as cursor:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userId UUID PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT,
        phone_number TEXT,
        generated BOOLEAN DEFAULT FALSE,
        google_id TEXT UNIQUE,
        profile_picture TEXT,
        auth_provider TEXT DEFAULT 'email',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
    
    # Add phone_number column if it doesn't exist (for existing databases)
    try:
        cursor.execute('''
            ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number TEXT
        ''')
    except Exception as e:
        print(f"Note: phone_number column may already exist: {e}")

def create_user(username, email, password, phone_number=None):
    for attempt in range(2):
        try:
            if any(user['email'] == email for user in users):
                print(f"User with email {email} already exists.")
                return
            user_id = str(uuid.uuid4())
            new_user = {
                "userId": user_id,
                "username": username,
                "email": email,
                "password": password,
                "phone_number": phone_number,
            }
            users.append(new_user)
            with get_db_connection() as cursor:
                cursor.execute("INSERT INTO users (userId, username, email, password, phone_number) VALUES (%s, %s, %s, %s, %s)",
                           (user_id, username, email, password, phone_number))
            print(f"User {user_id} added.")
            return new_user
        except psycopg2.InterfaceError as e:
            print(f"[create_user] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in create_user: {e}")
            return None
    return None

def get_user(user_id):
    for user in users:
        if user["userId"] == user_id:
            return user
    
    # Try up to 2 times with connection reset
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM users WHERE userId = %s", (user_id,))
                row = cursor.fetchone()
                if row:
                    # Get column names from cursor description
                    column_names = [desc[0] for desc in cursor.description]
                    # Create dictionary from row and column names
                    return dict(zip(column_names, row))
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
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
                if row:
                    # Get column names from cursor description
                    column_names = [desc[0] for desc in cursor.description]
                    # Create dictionary from row and column names
                    return dict(zip(column_names, row))
                print(f"User with email {email} not found.")
                return None
        except psycopg2.InterfaceError as e:
            print(f"[get_user_from_email] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_user_from_email: {e}")
            return None
    return None

def get_user_by_google_id(google_id):
    """Get user by Google ID"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
                row = cursor.fetchone()
                if row:
                    # Get column names from cursor description
                    column_names = [desc[0] for desc in cursor.description]
                    # Create dictionary from row and column names
                    return dict(zip(column_names, row))
                print(f"User with Google ID {google_id} not found.")
                return None
        except psycopg2.InterfaceError as e:
            print(f"[get_user_by_google_id] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_user_by_google_id: {e}")
            return None
    return None

def create_google_user(google_id, email, name, profile_picture):
    """Create a new user with Google authentication"""
    for attempt in range(2):
        try:
            # Check if user already exists
            existing_user = get_user_by_google_id(google_id)
            if existing_user:
                print(f"User with Google ID {google_id} already exists.")
                return existing_user
            
            # Check if email already exists
            existing_user = get_user_from_email(email)
            if existing_user:
                print(f"User with email {email} already exists.")
                return existing_user
            
            user_id = str(uuid.uuid4())
            new_user = {
                "userId": user_id,
                "username": name,
                "email": email,
                "password": None,
                "phone_number": None,
                "google_id": google_id,
                "profile_picture": profile_picture,
                "auth_provider": "google"
            }
            
            with get_db_connection() as cursor:
                cursor.execute("""
                INSERT INTO users (userId, username, email, password, phone_number, google_id, profile_picture, auth_provider)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, email, None, None, google_id, profile_picture, "google"))
           
            print(f"Google user {user_id} added.")
            return new_user
        except psycopg2.InterfaceError as e:
            print(f"[create_google_user] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in create_google_user: {e}")
            return None
    return None


def get_all_users():
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
                if not rows:
                    return []
                
                # Get column names from cursor description
                column_names = [desc[0] for desc in cursor.description]
                
                # Create dictionaries from rows and column names
                return [dict(zip(column_names, row)) for row in rows]
        except psycopg2.InterfaceError as e:
            print(f"[get_all_users] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_all_users: {e}")
            return []
    return []


def update_user(user_id, updated_info):
    for user in users:
        if user["userId"] == user_id:
            user.update(updated_info)
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                for key in ["username", "email", "password"]:
                    if key in updated_info:
                        cursor.execute(f"UPDATE users SET {key} = %s WHERE userId = %s", (updated_info[key], user_id))
                
                print(f"User {user_id} updated.")
                return "Done"
        except psycopg2.InterfaceError as e:
            print(f"[update_user] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in update_user: {e}")
            return None
    print(f"User {user_id} not found.")
    return None

def delete_user(user_id):
    for i, user in enumerate(users):
        if user["userId"] == user_id:
            del users[i]
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("DELETE FROM users WHERE userId = %s", (user_id,))
                
                print(f"User {user_id} deleted.")
                return "Done"
        except psycopg2.InterfaceError as e:
            print(f"[delete_user] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in delete_user: {e}")
            return None
    print(f"User {user_id} not found.")
    return None

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

def ensure_tables_exist():
    """Ensure all required tables exist in the database"""
    try:
        with get_db_connection() as cursor:
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
                payment_status BOOLEAN DEFAULT FALSE,
                premium BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
            )
            ''')
            print("Tables ensured successfully")
    except Exception as e:
        print(f"Error ensuring tables exist: {e}")

# Initialize tables when module is imported (but don't block import)
try:
    ensure_tables_exist()
except Exception as e:
    print(f"Warning: Could not initialize tables during import: {e}")

def check_user_generated_status(user_id):
    """Check if a user has already generated a brand"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT generated FROM users WHERE userId = %s", (user_id,))
                row = cursor.fetchone()
                if row:
                    return row[0]  # Return the generated boolean value
                return None  # User not found
        except psycopg2.Error as e:
            print(f"Database error in check_user_generated_status (attempt {attempt + 1}): {e}")
            if attempt == 0:  # Only reset on first failure
                reset_connection()
            else:
                return None
    return None

def update_user_generated_status(user_id, generated_status):
    """Update the generated status of a user"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("UPDATE users SET generated = %s WHERE userId = %s", (generated_status, user_id))
                return True
        except psycopg2.Error as e:
            print(f"Database error in update_user_generated_status (attempt {attempt + 1}): {e}")
            if attempt == 0:  # Only reset on first failure
                reset_connection()
            else:
                return False
    return False

def create_brand(user_id):
    # First check if user has already generated a brand
    generated_status = check_user_generated_status(user_id)
    if generated_status is None:
        print(f"User {user_id} not found.")
        return None
    
    if generated_status:
        print(f"User {user_id} has already generated a brand.")
        return None
    
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
        "payment_status": False,
    }
    try:
        with get_db_connection() as cursor:
            cursor.execute("""
            INSERT INTO brands (id, userId, answerId, name, logo, brand_strategy, brand_communication, brand_identity, marketing_and_social_media_strategy, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            new_brand["id"], new_brand["userId"], new_brand["answerId"], new_brand["name"],
            new_brand["logo"], new_brand["brand_strategy"], new_brand["brand_communication"],
            new_brand["brand_identity"], new_brand["marketing_and_social_media_strategy"], new_brand["payment_status"]
        ))
            
            # Update user's generated status to True
            cursor.execute("UPDATE users SET generated = TRUE WHERE userId = %s", (user_id,))
        
        print(f"Brand {brand_id} created for user {user_id} and generated status updated.")
        return new_brand
    except psycopg2.IntegrityError as e:
        print(f"Error creating brand: {e}")
        
        return None

def get_brand(brand_id):
    # Try up to 2 times with connection reset
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get column names from cursor description
                column_names = [desc[0] for desc in cursor.description]
                
                # Create dictionary from row and column names
                return dict(zip(column_names, row))
        except psycopg2.Error as e:
            print(f"Database error in get_brand (attempt {attempt + 1}): {e}")
            if attempt == 0:  # Only reset on first failure
                reset_connection()
            else:
                return None
    
    return None

def get_all_user_brands(user_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT * FROM brands WHERE userId = %s", (user_id,))
                rows = cursor.fetchall()
                if not rows:
                    return []
                
                # Get column names from cursor description
                column_names = [desc[0] for desc in cursor.description]
                
                # Create dictionaries from rows and column names
                return [dict(zip(column_names, row)) for row in rows]
        except psycopg2.InterfaceError as e:
            print(f"[get_all_user_brands] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in get_all_user_brands: {e}")
            return []
    return []

def update_brand(brand_id, property_name, new_value):
    allowed_properties = [
        "name", "logo", "answerId", "brand_strategy", "brand_communication",
        "brand_identity", "marketing_and_social_media_strategy", "payment_status"
    ]
    if property_name not in allowed_properties:
        raise ValueError(f"Invalid or non-updatable property: {property_name}")
    query = f"UPDATE brands SET {property_name} = %s WHERE id = %s"
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute(query, (new_value, brand_id))
                
                if cursor.rowcount == 0:
                    print(f"Brand {brand_id} not found or value was not changed.")
                    return None
                print(f"Brand {brand_id} property '{property_name}' updated.")
                return get_brand(brand_id)
        except psycopg2.InterfaceError as e:
            print(f"[update_brand] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in update_brand: {e}")
            return None
    return None

def delete_brand(brand_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("DELETE FROM brands WHERE id = %s", (brand_id,))
                
                if cursor.rowcount > 0:
                    print(f"Brand {brand_id} has been deleted.")
                    return True
                else:
                    print(f"Brand {brand_id} not found.")
                    return False
        except psycopg2.InterfaceError as e:
            print(f"[delete_brand] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in delete_brand: {e}")
            return False
    return False

def check_brand_payment_status(brand_id):
    """Check if a brand has been paid for"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("SELECT payment_status FROM brands WHERE id = %s", (brand_id,))
                row = cursor.fetchone()
                if row:
                    return row[0]  # Returns True/False
                return None  # Brand not found
        except psycopg2.InterfaceError as e:
            print(f"[check_brand_payment_status] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in check_brand_payment_status: {e}")
            return None
    return None

def update_brand_payment_status(brand_id, payment_status):
    """Update the payment status of a brand"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("UPDATE brands SET payment_status = %s WHERE id = %s", (payment_status, brand_id))
                
                if cursor.rowcount == 0:
                    print(f"Brand {brand_id} not found or payment status was not changed.")
                    return False
                print(f"Brand {brand_id} payment status updated to: {payment_status}")
                return True
        except psycopg2.InterfaceError as e:
            print(f"[update_brand_payment_status] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error in update_brand_payment_status: {e}")
            return False
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

# Wrap table creation in try-except to prevent import errors
try:
    with get_db_connection() as cursor:
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
    with get_db_connection() as cursor:
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

        # Table to store paid brand assets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_assets (
                id UUID PRIMARY KEY,
                brandId UUID NOT NULL,
                userId UUID NOT NULL,
                full_brand_identity JSONB,
                social_media_content JSONB,
                premium_assets JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brandId) REFERENCES brands(id) ON DELETE CASCADE,
                FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
            )
        ''')
        
        # Add premium_assets column if it doesn't exist (for existing databases)
        try:
            cursor.execute('''
                ALTER TABLE brand_assets 
                ADD COLUMN IF NOT EXISTS premium_assets JSONB
            ''')
        except Exception as e:
            print(f"Note: premium_assets column may already exist: {e}")
except Exception as e:
    print(f"Note: Database tables may already exist or connection not available during import: {e}")

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
        with get_db_connection() as cursor:
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
            print(f"Answer object {answer_id} created for user {user_id}.")
            
            # Construct the result directly instead of calling get_answer
            result = {
                "answerId": answer_id,
                "userId": user_id,
                "sections": []
            }
            
            # Get the sections we just created
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
                
                # Get the questions for this section
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
        print(f"[create_answers] InterfaceError: {e}. Retrying once.")
        try:
            with get_db_connection() as cursor:
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
                print(f"Answer object {answer_id} created for user {user_id} (after retry).")
                
                # Construct the result directly instead of calling get_answer
                result = {
                    "answerId": answer_id,
                    "userId": user_id,
                    "sections": []
                }
                
                # Get the sections we just created
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
                    
                    # Get the questions for this section
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
        except Exception as e2:
            print(f"Database error during answer creation after retry: {e2}")
            return None
    except psycopg2.Error as e:
        print(f"Database error during answer creation: {e.pgerror}")
        return None

def get_answer(answer_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
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
            with get_db_connection() as cursor:
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
        with get_db_connection() as cursor:
            cursor.execute(query, (answer_id, limit_global_question_number))
            rows = cursor.fetchall()
            print(f"  SQL result rows: {rows}")
            result = [row[0] for row in rows]
            print(f"  Final result: {result}")
            return result
    except psycopg2.InterfaceError as e:
        print(f"[get_previous_answers] InterfaceError: {e}. Retrying once.")
        try:
            with get_db_connection() as cursor:
                cursor.execute(query, (answer_id, limit_global_question_number))
                rows = cursor.fetchall()
                print(f"  SQL result rows (after retry): {rows}")
                result = [row[0] for row in rows]
                print(f"  Final result (after retry): {result}")
                return result
        except Exception as e2:
            print(f"  Database error in get_previous_answers after retry: {e2}")
            return []
    except psycopg2.Error as e:
        print(f"  Database error in get_previous_answers: {e}")
        reset_connection()
        return []

def update_answer(answer_id, global_question_number, new_text):
    try:
        print(f"[update_answer] Attempting update: answer_id={answer_id}, global_question_number={global_question_number}, new_text={new_text}")
        with get_db_connection() as cursor:
            cursor.execute("""
                UPDATE answers_questions
                SET answer_text = %s
                WHERE global_question_number = %s AND sectionId_fk IN (
                    SELECT sectionId FROM answers_sections WHERE answerId_fk = %s
                )
            """, (new_text, global_question_number, answer_id))
            
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
                    
                    print(f"[update_answer] Inserted new answer for answer_id={answer_id}, global_question_number={global_question_number}.")
                    return True
                except psycopg2.Error as e:
                    print(f"[update_answer] Database error during upsert: {e}")
                   
                    return {'error': f'Database error during upsert: {e}'}
    except psycopg2.InterfaceError as e:
        print(f"[update_answer] InterfaceError: {e}. Retrying once.")
        try:
            with get_db_connection() as cursor:
                cursor.execute("""
                    UPDATE answers_questions
                    SET answer_text = %s
                    WHERE global_question_number = %s AND sectionId_fk IN (
                        SELECT sectionId FROM answers_sections WHERE answerId_fk = %s
                    )
                """, (new_text, global_question_number, answer_id))
                if cursor.rowcount > 0:
                    print(f"[update_answer] Answer updated successfully for answer_id={answer_id}, global_question_number={global_question_number} (after retry).")
                    return True
                else:
                    print(f"[update_answer] No answer found to update for answer_id={answer_id}, global_question_number={global_question_number} (after retry). Attempting upsert...")
                    section_number, answer_number = get_section_and_answer_number(global_question_number)
                    cursor.execute("SELECT sectionId FROM answers_sections WHERE answerId_fk = %s AND section_number = %s", (answer_id, section_number))
                    section_row = cursor.fetchone()
                    if not section_row:
                        print(f"[update_answer] No section found for answer_id={answer_id}, section_number={section_number} (after retry). Cannot upsert.")
                        return {'error': f'No section found for answer_id={answer_id}, section_number={section_number} (after retry). Cannot upsert.'}
                    section_id = section_row[0]
                    try:
                        cursor.execute("""
                            INSERT INTO answers_questions (sectionId_fk, answer_number, global_question_number, answer_text)
                            VALUES (%s, %s, %s, %s)
                        """, (section_id, answer_number, global_question_number, new_text))
                        print(f"[update_answer] Inserted new answer for answer_id={answer_id}, global_question_number={global_question_number} (after retry).")
                        return True
                    except psycopg2.Error as e2:
                        print(f"[update_answer] Database error during upsert after retry: {e2}")
                        return {'error': f'Database error during upsert after retry: {e2}'}
        except Exception as e2:
            print(f"[update_answer] Database error during answer update after retry: {e2}")
            return {'error': f'Database error during answer update after retry: {e2}'}
    except psycopg2.Error as e:
        print(f"[update_answer] Database error during answer update: {e}")
        
        return {'error': f'Database error during answer update: {e}'}

def delete_answer(answer_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("DELETE FROM answers_main WHERE answerId = %s", (answer_id,))
                
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
            return False
        return False
    
        return False
    
# ===================== Cloudinary Image Management ===========================================

def save_image_url(answer_id, section_number, question_number, cloudinary_url, cloudinary_public_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("""
                    INSERT INTO answer_images (answerId_fk, section_number, question_number, cloudinary_url, cloudinary_public_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (answerId_fk, section_number, question_number)
                    DO UPDATE SET 
                        cloudinary_url = EXCLUDED.cloudinary_url,
                        cloudinary_public_id = EXCLUDED.cloudinary_public_id,
                        created_at = CURRENT_TIMESTAMP
                """, (answer_id, section_number, question_number, cloudinary_url, cloudinary_public_id))
                
                print(f"Image URL saved for answer {answer_id}, section {section_number}, question {question_number}")
                return True
        except psycopg2.InterfaceError as e:
            print(f"[save_image_url] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error saving image URL: {e}")
           
            return False
    return False

def get_image_url(answer_id, section_number, question_number):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
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
            with get_db_connection() as cursor:
                cursor.execute("""
                    DELETE FROM answer_images
                    WHERE answerId_fk = %s AND section_number = %s AND question_number = %s
                """, (answer_id, section_number, question_number))
                
                if cursor.rowcount > 0:
                    print(f"Image URL deleted for answer {answer_id}, section {section_number}, question {question_number}")
                    return True
                return False
        except psycopg2.InterfaceError as e:
            print(f"[delete_image_url] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error deleting image URL: {e}")
            
            return False
    return False

def get_all_images_for_answer(answer_id):
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
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

# ===================== Brand Assets Management ===========================================

def create_brand_assets(brand_id, user_id, full_brand_identity, social_media_content, premium_assets=None):
    """Create or update brand assets for paid users"""
    asset_id = str(uuid.uuid4())
    
    # First, try to determine the correct column name
    try:
        with get_db_connection() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'brand_assets' AND column_name ILIKE 'userid'
                ORDER BY column_name
            """)
            columns = cursor.fetchall()
            user_id_column = None
            for col in columns:
                if col[0] == 'userId':
                    user_id_column = 'userId'
                    break
                elif col[0] == 'userid':
                    user_id_column = 'userid'
                    break
            
            if not user_id_column:
                print("WARNING: Could not determine user ID column name, defaulting to 'userId'")
                user_id_column = 'userId'
            
            print(f"Using column name: {user_id_column}")
            
            # Use the correct column name in the query
            # First try to insert, if it fails due to existing record, then update
            try:
                cursor.execute(f"""
                    INSERT INTO brand_assets (id, brandId, {user_id_column}, full_brand_identity, social_media_content, premium_assets)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (asset_id, brand_id, user_id, json.dumps(full_brand_identity), json.dumps(social_media_content), json.dumps(premium_assets) if premium_assets else None))
            except psycopg2.IntegrityError as e:
                # If insert fails due to duplicate brandId, update instead
                if "duplicate key" in str(e) or "unique constraint" in str(e):
                    cursor.execute(f"""
                        UPDATE brand_assets 
                        SET {user_id_column} = %s,
                            full_brand_identity = %s,
                            social_media_content = %s,
                            premium_assets = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE brandId = %s
                    """, (user_id, json.dumps(full_brand_identity), json.dumps(social_media_content), json.dumps(premium_assets) if premium_assets else None, brand_id))
                else:
                    # Re-raise if it's a different integrity error
                    raise
            print(f"Brand assets created/updated for brand {brand_id} and user {user_id}")
            return asset_id
    except psycopg2.Error as e:
        print(f"Database error creating brand assets: {e}")
        return None

def get_brand_assets(brand_id):
    """Get brand assets for a specific brand"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                # First, try to determine the correct column name
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'brand_assets' AND column_name ILIKE 'userid'
                    ORDER BY column_name
                """)
                columns = cursor.fetchall()
                user_id_column = None
                for col in columns:
                    if col[0] == 'userId':
                        user_id_column = 'userId'
                        break
                    elif col[0] == 'userid':
                        user_id_column = 'userid'
                        break
                
                if not user_id_column:
                    print("WARNING: Could not determine user ID column name, defaulting to 'userId'")
                    user_id_column = 'userId'
                
                cursor.execute(f"""
                    SELECT id, brandId, {user_id_column}, full_brand_identity, social_media_content, premium_assets, created_at, updated_at
                    FROM brand_assets 
                    WHERE brandId = %s
                """, (brand_id,))
                row = cursor.fetchone()
                if row:
                    # Helper function to safely parse JSON fields
                    def safe_json_loads(value):
                        if value is None:
                            return None
                        if isinstance(value, dict):
                            return value
                        if isinstance(value, str):
                            try:
                                return json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                return value
                        return value
                    
                    return {
                        "id": row[0],
                        "brandId": row[1],
                        "userId": row[2],
                        "full_brand_identity": safe_json_loads(row[3]),
                        "social_media_content": safe_json_loads(row[4]),
                        "premium_assets": safe_json_loads(row[5]),
                        "created_at": row[6],
                        "updated_at": row[7]
                    }
                return None
        except psycopg2.InterfaceError as e:
            print(f"[get_brand_assets] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error getting brand assets: {e}")
            return None
    return None

def get_brand_assets_by_user(user_id):
    """Get all brand assets for a specific user"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                # First, try to determine the correct column name
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'brand_assets' AND column_name ILIKE 'userid'
                    ORDER BY column_name
                """)
                columns = cursor.fetchall()
                user_id_column = None
                for col in columns:
                    if col[0] == 'userId':
                        user_id_column = 'userId'
                        break
                    elif col[0] == 'userid':
                        user_id_column = 'userid'
                        break
                
                if not user_id_column:
                    print("WARNING: Could not determine user ID column name, defaulting to 'userId'")
                    user_id_column = 'userId'
                
                cursor.execute(f"""
                    SELECT id, brandId, {user_id_column}, full_brand_identity, social_media_content, premium_assets, created_at, updated_at
                    FROM brand_assets 
                    WHERE {user_id_column} = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                rows = cursor.fetchall()
                
                # Helper function to safely parse JSON fields
                def safe_json_loads(value):
                    if value is None:
                        return None
                    if isinstance(value, dict):
                        return value
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    return value
                
                return [
                    {
                        "id": row[0],
                        "brandId": row[1],
                        "userId": row[2],
                        "full_brand_identity": safe_json_loads(row[3]),
                        "social_media_content": safe_json_loads(row[4]),
                        "premium_assets": safe_json_loads(row[5]),
                        "created_at": row[6],
                        "updated_at": row[7]
                    }
                    for row in rows
                ]
        except psycopg2.InterfaceError as e:
            print(f"[get_brand_assets_by_user] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error getting brand assets by user: {e}")
            return []
    return []

def delete_brand_assets(brand_id):
    """Delete brand assets for a specific brand"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                cursor.execute("DELETE FROM brand_assets WHERE brandId = %s", (brand_id,))
                if cursor.rowcount > 0:
                    print(f"Brand assets deleted for brand {brand_id}")
                    return True
                return False
        except psycopg2.InterfaceError as e:
            print(f"[delete_brand_assets] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error deleting brand assets: {e}")
            return False
    return False

def check_brand_assets_table_structure():
    """Check the actual column names in the brand_assets table"""
    try:
        with get_db_connection() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'brand_assets'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("brand_assets table structure:")
            for column in columns:
                print(f"  {column[0]} ({column[1]})")
            return columns
    except psycopg2.Error as e:
        print(f"Error checking brand_assets table structure: {e}")
        return None

def get_full_brand(brand_id):
    """Get complete brand information including brand details and brand assets"""
    for attempt in range(2):
        try:
            with get_db_connection() as cursor:
                # Get brand information
                cursor.execute("SELECT * FROM brands WHERE id = %s", (brand_id,))
                brand_row = cursor.fetchone()
                
                if not brand_row:
                    return None
                
                # Get column names from cursor description
                brand_column_names = [desc[0] for desc in cursor.description]
                brand_data = dict(zip(brand_column_names, brand_row))
                
                # Helper function to safely parse JSON fields
                def safe_json_loads(value):
                    if value is None:
                        return None
                    if isinstance(value, dict):
                        return value
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    return value
                
                # Parse JSON fields in brand data
                json_fields = ['brand_strategy', 'brand_communication', 'brand_identity', 'marketing_and_social_media_strategy']
                for field in json_fields:
                    if field in brand_data and brand_data[field]:
                        brand_data[field] = safe_json_loads(brand_data[field])
                
                # Get brand assets information
                # First, try to determine the correct column name for user_id
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'brand_assets' AND column_name ILIKE 'userid'
                    ORDER BY column_name
                """)
                columns = cursor.fetchall()
                user_id_column = None
                for col in columns:
                    if col[0] == 'userId':
                        user_id_column = 'userId'
                        break
                    elif col[0] == 'userid':
                        user_id_column = 'userid'
                        break
                
                if not user_id_column:
                    print("WARNING: Could not determine user ID column name, defaulting to 'userId'")
                    user_id_column = 'userId'
                
                cursor.execute(f"""
                    SELECT id, brandId, {user_id_column}, full_brand_identity, social_media_content, premium_assets, created_at, updated_at
                    FROM brand_assets 
                    WHERE brandId = %s
                """, (brand_id,))
                assets_row = cursor.fetchone()
                
                brand_assets_data = None
                if assets_row:
                    # Helper function to safely parse JSON fields
                    def safe_json_loads(value):
                        if value is None:
                            return None
                        if isinstance(value, dict):
                            return value
                        if isinstance(value, str):
                            try:
                                return json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                return value
                        return value
                    
                    brand_assets_data = {
                        "id": assets_row[0],
                        "brandId": assets_row[1],
                        "userId": assets_row[2],
                        "full_brand_identity": safe_json_loads(assets_row[3]),
                        "social_media_content": safe_json_loads(assets_row[4]),
                        "premium_assets": safe_json_loads(assets_row[5]),
                        "created_at": assets_row[6],
                        "updated_at": assets_row[7]
                    }
                
                # Combine brand and assets data
                full_brand = {
                    "brand": brand_data,
                    "brand_assets": brand_assets_data
                }
                
                return full_brand
                
        except psycopg2.InterfaceError as e:
            print(f"[get_full_brand] InterfaceError: {e}. Resetting connection and retrying once.")
            reset_connection()
        except psycopg2.Error as e:
            print(f"Database error getting full brand: {e}")
            return None
    return None