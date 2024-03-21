"""Password manager"""
import os
import random
import sqlite3
import string
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror, showinfo

from cryptography.fernet import Fernet, InvalidToken
from customtkinter import (CTk, CTkButton, CTkCheckBox, CTkEntry, CTkFrame,
                           CTkLabel, CTkScrollableFrame, CTkTextbox)

root = CTk()
root.title('Login to get passwords')
root.geometry('1080x790')
root.columnconfigure(0, weight=2)

current_key: bytes = bytes()

def register_new_key():
    """Register new key"""
    global current_key
    key = Fernet.generate_key()
    current_key = key
    with open('password_manager.key', 'wb') as key_file:
        key_file.write(key)
    showinfo('New key generated', f'Key file is at {os.path.abspath("password_manager.key")}')
    if os.path.exists('database.sqlite3'):
        os.remove('database.sqlite3')
    load_passwords()

def login():
    """Login to password manager"""
    global current_key
    try:
        with open(askopenfilename(defaultextension='key', initialdir='.'),
                encoding='utf-8') as key_file:
            if not os.path.splitext(key_file.name)[1] == '.key':
                showerror('Wrong key file', 'Key file must be a .key file')
                return
            key: bytes = key_file.read()
            current_key = key
    except TypeError:
        pass
    load_passwords()


def insert_password(_=None):
    """Insert a new password in the database"""
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    if any(not i for i in (website, username, password)):
        return
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    fernet = Fernet(current_key)
    cursor.execute('INSERT INTO passwords VALUES (?, ?, ?)', (
        website, username, fernet.encrypt(password.encode('utf-8'))
    ))
    conn.commit()
    conn.close()
    load_passwords()
    website_entry.delete(0, 'end')
    username_entry.delete(0, 'end')
    password_entry.delete(0, 'end')


def load_password_ui(website: str, username: str, password: str, i:int):
    """Load the single password entry UI"""
    entry_frame = CTkFrame(passwords_frame, width=680, height=200)
    entry_frame.columnconfigure(0, weight=2)
    website_label = CTkLabel(entry_frame, text=website, font=('Segoe UI', 18, 'bold'))
    website_label.grid(row=0, column=0, padx=20, pady=10, sticky='nsew', rowspan=2)
    username_label = CTkLabel(entry_frame, text=username, font=('Segoe UI', 18, 'bold'))
    username_label.grid(row=0, column=1, padx=20, pady=10, sticky='nsew', rowspan=2)
    password_label = CTkLabel(entry_frame, text=password, font=('Segoe UI', 18, 'bold'))
    password_label.grid(row=0, column=2, padx=20, pady=10, sticky='nsew', rowspan=2)
    edit_website_entry = CTkEntry(entry_frame, width=140, height=40, placeholder_text='Website',
                                font=('Segoe UI', 16))
    edit_username_entry = CTkEntry(entry_frame, width=140, height=40, placeholder_text='Username',
                                font=('Segoe UI', 16))
    edit_password_entry = CTkEntry(entry_frame, width=140, height=40, placeholder_text='Password',
                                font=('Segoe UI', 16))
    submit_edits_btn = CTkButton(entry_frame, width=20, height=20, text='OK',
        font=('Segoe UI', 18, 'bold'),
        command=lambda: edit_password(edit_website_entry.get(), edit_username_entry.get(),
                    edit_password_entry.get(),
                    website, username,
                    edit_website_entry, edit_username_entry, edit_password_entry))
    edit_password_btn = CTkButton(entry_frame, text='Edit',
        fg_color='blue', width=50, height=20,
        font=('Segoe UI', 15, 'bold'),
        command=lambda: [
            website_label.grid_forget(),
            username_label.grid_forget(),
            password_label.grid_forget(),
            edit_website_entry.insert(0, website),
            edit_username_entry.insert(0, username),
            edit_password_entry.insert(0, password),
            edit_website_entry.grid(row=0, column=0, padx=15, pady=10, sticky='nsew'),
            edit_username_entry.grid(row=0, column=1, padx=15, pady=10, sticky='nsew'),
            edit_password_entry.grid(row=0, column=2, padx=15, pady=10, sticky='nsew'),
            submit_edits_btn.grid(row=0, column=5, padx=5, pady=10, sticky='nsew'),
            root.unbind('<Return>')
            ])
    edit_password_btn.grid(row=0, column=3, padx=15, pady=10)
    delete_password_btn = CTkButton(entry_frame, text='Delete', fg_color='red', width=50, height=20,
            font=('Segoe UI', 15, 'bold'),
            command=lambda: [delete_password(website, username), entry_frame.destroy()])
    delete_password_btn.grid(row=1, column=3, padx=15, pady=10)
    entry_frame.grid(row=i, column=0, padx=15, pady=15, sticky='new')

def load_ui():
    """Load the UI components"""
    actions_frame.grid(row=0, column=0, padx=10, pady=10, sticky='new')
    password_generator.grid(row=1, column=0, padx=10, pady=20, sticky='new')
    passwords_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsw', rowspan=2)


def load_passwords():
    """Load all the passwords in the UI"""
    login_frame.pack_forget()
    load_ui()
    fernet = Fernet(current_key)
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS passwords (website TEXT, username TEXT, password BLOB)'
    )
    conn.commit()
    cursor.execute('SELECT * FROM passwords')
    passwords = cursor.fetchall()
    for i, entry in enumerate(passwords):
        website: str = entry[0]
        username: str = entry[1]
        try:
            password: str = fernet.decrypt(entry[2]).decode('utf-8')
        except (InvalidToken, ValueError):
            showerror('Invalid key file', 'Register a new key or use the correct one!')
            for widget in root.winfo_children():
                widget.grid_forget()
            login_frame.pack(anchor='center')
            return
        load_password_ui(website, username, password, i)
    conn.close()


def edit_password(website: str, username: str, password: str,
                old_website: str, old_username: str, *widgets):
    """Edit password from the database"""
    fernet = Fernet(current_key)
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''UPDATE passwords SET website = ?, username = ?, password = ?
            WHERE website = ? AND username = ?''',
            (website, username, fernet.encrypt(password.encode('utf-8')),
            old_website, old_username))
    conn.commit()
    conn.close()
    for widget in widgets:
        widget.grid_forget()
    load_passwords()
    root.bind('<Return>', insert_password)

def delete_password(website: str, username: str):
    """Delete a password from the database"""
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM passwords WHERE website = ? AND username = ?',
            (website, username))
    conn.commit()
    conn.close()
    load_passwords()

def generate_password():
    length = int(length_entry.get())
    characters = ''
    if uppercase_check.get():
        characters += string.ascii_uppercase
    if lowercase_check.get():
        characters += string.ascii_lowercase
    if digits_check.get():
        characters += string.digits
    if special_chars_check.get():
        characters += string.punctuation
    if not characters:
        return
    password = ''.join(random.choice(characters) for _ in range(length))
    password_label.configure(state='normal')
    password_label.delete('1.0', 'end')
    password_label.insert('1.0', text=password)
    password_label.configure(state='disabled')


def validate_input(new_value):
    # Check if the new value is empty or consists of digits
    return new_value.isdigit() or new_value == ""

validate_digits = root.register(validate_input)


login_frame = CTkFrame(root, height=400, width=400)
login_label = CTkLabel(login_frame, text='Use your key file to get passwords',
                    font=('Segoe UI', 18, 'bold'))
login_label.grid(row=0, column=0, sticky='new', padx=25, pady=30)
key_button = CTkButton(login_frame, text='Upload',
                    font=('Segoe UI', 16), command=login)
key_button.grid(row=1, column=0, sticky='new', padx=25, pady=5)
register_button = CTkButton(login_frame, text='New key',
                    font=('Segoe UI', 16), command=register_new_key)
register_button.grid(row=2, column=0, sticky='new', padx=25, pady=5)
login_frame.pack(anchor='center')

actions_frame = CTkFrame(root, width=150, height=540)
actions_label = CTkLabel(actions_frame, text='Actions', font=('Segoe UI', 18, 'bold'))
actions_label.grid(row=0, column=0, sticky='new', padx=25, pady=10)
website_entry = CTkEntry(actions_frame, width=200, height=40,
                        placeholder_text='Website', font=('Segoe UI', 16))
website_entry.grid(row=0, column=0, sticky='new', padx=10, pady=10)
username_entry = CTkEntry(actions_frame, width=200, height=40,
                        placeholder_text='Username', font=('Segoe UI', 16))
username_entry.grid(row=1, column=0, sticky='new', padx=10, pady=10)
password_entry = CTkEntry(actions_frame, width=200, height=40,
                        placeholder_text='Password', font=('Segoe UI', 16))
password_entry.grid(row=2, column=0, sticky='new', padx=10, pady=10)
submit_button = CTkButton(actions_frame, width=120, height=40, text='Submit',
                        font=('Segoe UI', 16), command=insert_password)
submit_button.grid(row=3, column=0, sticky='new', padx=10, pady=10)
root.bind('<Return>', insert_password)

password_generator = CTkFrame(root, width=150, height=540)
password_generator_label = CTkLabel(password_generator, text='Password generator',
                                font=('Segoe UI', 15, 'bold'))
password_generator_label.grid(row=0, column=0, sticky='nsew', padx=25, pady=10)
length_entry = CTkEntry(password_generator, placeholder_text='Length', validate='key',
                validatecommand=(validate_digits, '%P'), font=('Segoe UI', 15), width=20, height=40)
length_entry.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
uppercase_check = CTkCheckBox(password_generator, text='Uppercase', font=('Segoe UI', 13))
uppercase_check.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
lowercase_check = CTkCheckBox(password_generator, text='Lowercase', font=('Segoe UI', 13))
lowercase_check.grid(row=3, column=0, sticky='nsew', padx=10, pady=10)
digits_check = CTkCheckBox(password_generator, text='Digits', font=('Segoe UI', 13))
digits_check.grid(row=4, column=0, sticky='nsew', padx=10, pady=10)
special_chars_check = CTkCheckBox(password_generator, text='Special characters', font=('Segoe UI', 13))
special_chars_check.grid(row=5, column=0, sticky='nsew', padx=10, pady=10)
generate_btn = CTkButton(password_generator, width=120, height=40, text='Generate',
                        font=('Segoe UI', 16, 'bold'), command=generate_password)
generate_btn.grid(row=6, column=0, sticky='nsew', padx=10, pady=10)
password_label = CTkTextbox(password_generator, width=100, height=60,
                        font=('Segoe UI', 15, 'bold'))
password_label.configure(state='disabled')
password_label.grid(row=7, column=0, sticky='nsew', padx=10, pady=10)
copy_btn = CTkButton(password_generator, width=100, height=40, text='Copy', font=('Segoe UI', 15, 'bold'),
    command=lambda: [
    root.clipboard_clear(), root.clipboard_append(password_label.get('1.0', 'end-1c')),
    password_entry.insert(0, password_label.get('1.0', 'end-1c'))
])
copy_btn.grid(row=8, column=0, sticky='nsew', padx=10, pady=10)

passwords_frame = CTkScrollableFrame(root, width=800, height=680, fg_color='gray23')


if __name__ == '__main__':
    root.mainloop()
