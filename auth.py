import tkinter as tk
from tkinter import messagebox
import sqlite3
import subprocess
from PIL import Image, ImageTk

class AuthenticationSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.attributes('-fullscreen', True)  # Make the window fullscreen

        self.create_widgets()
        self.create_database()
        self.load_image()  # Load and display image
        self.display_quote()  # Display quote at bottom left corner

    def create_widgets(self):
        # Username Label and Entry
        self.username_label = tk.Label(self.root, text="Username:", font=('Helvetica', 16))
        self.username_label.place(x=30, y=300)

        self.username_entry = tk.Entry(self.root, font=('Helvetica', 16))
        self.username_entry.place(x=150, y=300)

        # Password Label and Entry
        self.password_label = tk.Label(self.root, text="Password:", font=('Helvetica', 16))
        self.password_label.place(x=30, y=330)

        self.password_entry = tk.Entry(self.root, show="*", font=('Helvetica', 16))
        self.password_entry.place(x=150, y=330)

        # Login Button
        self.login_button = tk.Button(self.root, text="Log In", command=self.login, width=10, font=('Helvetica', 12), bg='blue', fg='white')
        self.login_button.place(x=100, y=370)

        # Create Account Button
        self.create_account_button = tk.Button(self.root, text="Create Account", command=self.create_account, width=12, font=('Helvetica', 12), bg='green', fg='white')
        self.create_account_button.place(x=200, y=370)

    def create_database(self):
        self.conn = sqlite3.connect('authentication.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        password TEXT)''')
        self.conn.commit()

    def load_image(self):
        # Load and display image
        self.image = Image.open("img1.png")
        self.image = self.image.resize((950, 700), Image.BILINEAR)
        self.photo = ImageTk.PhotoImage(self.image)

        image_label = tk.Label(self.root, image=self.photo)
        image_label.image = self.photo
        image_label.place(x=350, y=0)

    def create_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username and password:
            self.c.execute("SELECT * FROM users WHERE username=?", (username,))
            if self.c.fetchone():
                messagebox.showerror("Error", "Username already exists!")
            else:
                self.c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                self.conn.commit()
                messagebox.showinfo("Success", "Account created successfully!")
        else:
            messagebox.showerror("Error", "Please enter both username and password.")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username and password:
            self.c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            if self.c.fetchone():
                messagebox.showinfo("Success", "Login successful!")
                self.launch_subprocess()
            else:
                messagebox.showerror("Error", "Invalid username or password.")
        else:
            messagebox.showerror("Error", "Please enter both username and password.")

    def launch_subprocess(self):
        subprocess.Popen(['python', 'sizeok.py'])

    def display_quote(self):
        quote_label = tk.Label(self.root, text="A room without books is like a body without a soul.", font=('Georgia', 20), wraplength=363, justify='left')
        quote_label.place(x=1, y=650)
        quote_label.config(fg="black", bg="burlywood3")  # Change text and background color

        # Increase font size and apply bold
        for i in range(14, 20):
            quote_label.config(font=('Georgia', i, 'bold'))
            self.root.update()
            self.root.after(100)  # Adjust the delay (milliseconds) to control the animation speed

if __name__ == "__main__":
    root = tk.Tk()
    app = AuthenticationSystem(root)
    root.mainloop()
