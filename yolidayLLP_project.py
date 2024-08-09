import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
from cryptography.fernet import Fernet
import os

# Load or generate encryption key
key_file_path = "secret.key"
if not os.path.exists(key_file_path):
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)
else:
    with open(key_file_path, "rb") as key_file:
        key = key_file.read()

cipher_suite = Fernet(key)

# MySQL Database setup
def create_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # Replace with your MySQL server host
            user='root',  # Replace with your MySQL username
            password='12344321',  # Replace with your MySQL password
            database='your_database'  # Replace with your MySQL database name
        )
        if conn.is_connected():
            st.success("Connected to MySQL database")
            return conn
        else:
            st.error("Connection failed")
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None


# Create tables if they don't exist
def create_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                doc_name VARCHAR(255),
                doc_content LONGBLOB,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                query TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        st.success("Tables created successfully")
    except Error as e:
        st.error(f"Error creating tables: {e}")



# User authentication
def user_auth(conn, username, password):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user:
            decrypted_password = cipher_suite.decrypt(user['password'].encode()).decode()
            if decrypted_password == password:
                return user
            else:
                st.error("Incorrect password")
                return None
        else:
            st.error("Username not found")
            return None
    except Error as e:
        st.error(f"Error during user authentication: {e}")
        return None


# User registration
def user_registration(conn, username, password):
    encrypted_password = cipher_suite.encrypt(password.encode())
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, encrypted_password.decode()))
        conn.commit()
        st.success("You have successfully created an account")
    except Error as e:
        st.error(f"Error during registration: {e}")

# Document upload
def upload_document(conn, user_id, doc_name, doc_content):
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO documents (user_id, doc_name, doc_content) VALUES (%s, %s, %s)', 
                       (user_id, doc_name, doc_content))
        conn.commit()
    except Error as e:
        st.error(f"Error during document upload: {e}")

# Document query
def query_documents(conn, user_id, query):
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT doc_content FROM documents WHERE user_id = %s', (user_id,))
        docs = cursor.fetchall()
        # Implement search functionality here
        response = "Implement your search logic here."
        return response
    except Error as e:
        st.error(f"Error querying documents: {e}")
        return None

# User history
def save_user_history(conn, user_id, query, response):
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (user_id, query, response) VALUES (%s, %s, %s)', 
                       (user_id, query, response))
        conn.commit()
    except Error as e:
        st.error(f"Error saving user history: {e}")

# Streamlit Interface
st.title("Document Query Application")

menu = ["Login", "Register", "Query Documents", "View History", "Download History"]
choice = st.sidebar.selectbox("Menu", menu)

conn = create_connection()
if conn:
    create_tables(conn)

if choice == "Login":
    st.subheader("Login Section")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = user_auth(conn, username, password)
        if user:
            st.success(f"Logged in as {username}")
        else:
            st.error("Invalid credentials")

elif choice == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("Register"):
        user_registration(conn, new_user, new_password)

elif choice == "Query Documents":
    st.subheader("Query Your Documents")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])
    query = st.text_input("Enter your query")
    if st.button("Search"):
        user_id = 1  # This should be replaced with the actual logged-in user ID
        if uploaded_file is not None:
            doc_content = uploaded_file.read()
            upload_document(conn, user_id, uploaded_file.name, doc_content)
            response = query_documents(conn, user_id, query)
            save_user_history(conn, user_id, query, response)
            st.write("Response:", response)
        else:
            st.error("Please upload a document first")

elif choice == "View History":
    st.subheader("Your Query History")
    user_id = 1  # This should be replaced with the actual logged-in user ID
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history WHERE user_id = %s', (user_id,))
        history = cursor.fetchall()
        st.write(pd.DataFrame(history, columns=["ID", "User ID", "Query", "Response", "Timestamp"]))
    except Error as e:
        st.error(f"Error retrieving history: {e}")

elif choice == "Download History":
    st.subheader("Download Your History")
    # Implement download functionality here
    st.write("Download functionality not implemented yet")
