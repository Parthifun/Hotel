import customtkinter as ctk
from tkinter import messagebox
import subprocess
from utils import DBAccess, hash_password, create_styled_frame
from constants import COLORS, FONTS, STYLES
from PIL import Image

def authenticate(username, password):
    hashed_pw = hash_password(password)
    query = "SELECT user_id, role FROM Users WHERE username = %s AND password = %s"
    result = DBAccess.execute_query(query, (username, hashed_pw))
    return result[0] if result else None

def on_login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Please fill in all fields")
        return

    try:
        user = authenticate(username, password)
        if user:
            role = 'host' if user['role'].lower() == 'host' else 'guest'
            subprocess.Popen(['python3', f'{role}_dashboard.py', str(user['user_id'])])
            login_window.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")
    except Exception as e:
        messagebox.showerror("Error", f"Login failed: {str(e)}")

def show_registration():
    subprocess.Popen(['python3', 'registration.py'])
    login_window.destroy()

def open_page(page):
    if page != "login":
        subprocess.Popen(['python3', f'{page}.py'])
        login_window.destroy()

def forgot_password():
    subprocess.Popen(['python3', 'forgot_password.py'])
    login_window.destroy()

def toggle_password():
    global show_password
    show_password = not show_password
    password_entry.configure(show="" if show_password else "*")
    toggle_button.configure(text="👁️" if show_password else "🙈")

# UI setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

login_window = ctk.CTk()
login_window.title("Food Event Login")
login_window.geometry("800x500")
login_window.configure(fg_color=COLORS['background'])

main_frame = create_styled_frame(login_window)
main_frame.pack(pady=25, padx=25, fill="both", expand=True)

main_frame.grid_rowconfigure(0, weight=0)
main_frame.grid_rowconfigure(1, weight=0)
main_frame.grid_rowconfigure(2, weight=1)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(
    main_frame,
    text="Food Event Platform",
    font=FONTS['title'],
    text_color=COLORS['primary']
).grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="nsew")

nav_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
nav_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)

button_style = {
    'font': FONTS['medium'],
    'text_color': "black",
    'fg_color': "transparent",
    'border_color': COLORS['primary'],
    'border_width': 1,
    'hover_color': COLORS['secondary']
}

for idx, (label, page) in enumerate([("Home", "home"), ("Contact Us", "contact"), ("Login", "login"), ("Sign Up", "registration")]):
    ctk.CTkButton(
        nav_frame,
        text=label,
        command=lambda p=page: open_page(p),
        **button_style
    ).grid(row=0, column=idx, padx=5)

left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
left_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

right_frame = ctk.CTkFrame(main_frame, fg_color="#e8f1e4")
right_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)

original_image = Image.open("images/login.jpg")
image_label = ctk.CTkLabel(left_frame, text="")
image_label.pack(expand=True, fill="both")

def resize_image(event):
    new_width = event.width
    new_height = event.height
    resized = original_image.resize((new_width, new_height), Image.LANCZOS)
    ctk_img = ctk.CTkImage(light_image=resized, size=(new_width, new_height))
    image_label.configure(image=ctk_img)
    image_label.image = ctk_img

left_frame.bind("<Configure>", resize_image)

ctk.CTkLabel(
    right_frame,
    text="LOGIN",
    font=FONTS['title'],
    text_color="black"
).pack(pady=(40, 20))

form_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
form_frame.pack(pady=10, padx=20)

# Username field
ctk.CTkLabel(
    form_frame,
    text="Username:",
    font=FONTS['medium'],
    text_color="black"
).pack(pady=(5, 2))

username_entry = ctk.CTkEntry(
    form_frame,
    width=STYLES['entry_width'],
    font=FONTS['medium'],
    corner_radius=STYLES['corner_radius'],
    fg_color="#dcdcdd",
    text_color="black"
)
username_entry.pack(pady=5)

# Password field
ctk.CTkLabel(
    form_frame,
    text="Password:",
    font=FONTS['medium'],
    text_color="black"
).pack(pady=(5, 2))

password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
password_frame.pack()

show_password = False

password_entry = ctk.CTkEntry(
    password_frame,
    show="*",
    width=STYLES['entry_width'] - 40,
    font=FONTS['medium'],
    corner_radius=STYLES['corner_radius'],
    fg_color="#dcdcdd",
    text_color="black"
)
password_entry.pack(side="left", padx=(0, 5))

toggle_button = ctk.CTkButton(
    password_frame,
    text="🙈",
    width=30,
    height=28,
    command=toggle_password,
    fg_color="#dcdcdd",
    text_color="black",
    hover=False
)
toggle_button.pack(side="left")

# Forgot password
ctk.CTkButton(
    form_frame,
    text="Forgot Password?",
    command=forgot_password,
    font=FONTS['small'],
    fg_color="transparent",
    text_color="blue",
    hover_color="#e0e0e0"
).pack(pady=(2, 10))

# Buttons
button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
button_frame.pack(pady=20)

ctk.CTkButton(
    button_frame,
    text="Login",
    command=on_login,
    width=STYLES['button_width'],
    font=FONTS['medium'],
    corner_radius=STYLES['corner_radius'],
    fg_color="#dcdcdd",
    text_color="black",
    hover_color="#e0e0e0"
).pack(pady=10)

ctk.CTkButton(
    button_frame,
    text="Create Account",
    command=show_registration,
    fg_color="transparent",
    border_color="black",
    border_width=1,
    text_color="black",
    hover_color="#1c7a9e"
).pack()

login_window.mainloop()
