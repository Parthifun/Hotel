import customtkinter as ctk
import sys
import subprocess
from tkinter import messagebox
from datetime import datetime
from utils import DBAccess, create_styled_frame
from constants import COLORS, FONTS, STYLES

def update_serving_size(event_id, people_change):
    try:
        DBAccess.execute_update(
            "UPDATE EVENTS SET serving_size = serving_size + %s WHERE event_id = %s",
            (people_change, event_id)
        )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update event: {str(e)}")

def cancel_booking(booking_id, event_id, num_people):
    if messagebox.askyesno("Confirm", "Cancel this booking?"):
        try:
            DBAccess.execute_update(
                "UPDATE bookings SET status = 'canceled' WHERE booking_id = %s",
                (booking_id,)
            )
            update_serving_size(event_id, num_people)
            messagebox.showinfo("Success", "Booking canceled")
            load_bookings()
        except Exception as e:
            messagebox.showerror("Error", f"Cancel failed: {str(e)}")

def edit_booking(booking_id, event_id, old_people, max_capacity, controls_frame):
    for widget in controls_frame.winfo_children():
        widget.destroy()

    edit_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    edit_frame.pack(pady=5)

    people_var = ctk.StringVar(value=str(old_people))
    entry = ctk.CTkEntry(edit_frame, textvariable=people_var, width=80,
                         validate="key", validatecommand=(window.register(lambda p: p.isdigit()), "%P"))
    entry.pack(side='left', padx=5)

    def save_changes():
        try:
            new_people = int(people_var.get())
            if new_people < 1:
                messagebox.showerror("Error", "Must book at least 1 person")
                return
            if new_people > max_capacity:
                messagebox.showerror("Error", f"Only {max_capacity} seats available")
                return

            difference = new_people - old_people
            DBAccess.execute_update(
                "UPDATE bookings SET number_of_attendees = %s WHERE booking_id = %s",
                (new_people, booking_id)
            )
            update_serving_size(event_id, -difference)
            messagebox.showinfo("Success", "Booking updated")
            load_bookings()
        except ValueError:
            messagebox.showerror("Error", "Invalid number")
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {str(e)}")

    ctk.CTkButton(edit_frame, text="Save", command=save_changes,
                  **STYLES['accent_button_small']).pack(side='left', padx=2)
    ctk.CTkButton(edit_frame, text="Cancel", command=load_bookings,
                  **STYLES['danger_button_small']).pack(side='left', padx=2)

def load_bookings():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    try:
        # Include paid_amount in the query
        bookings = DBAccess.execute_query("""
            SELECT b.booking_id, b.number_of_attendees, b.paid_amount, b.booking_time, b.status,
                   e.event_id, e.event_name, e.address, e.event_datetime,
                   e.serving_size + b.number_of_attendees AS total_capacity,
                   u.name AS host_name
            FROM bookings b
            JOIN EVENTS e ON b.event_id = e.event_id
            JOIN Users u ON e.host_id = u.user_id
            WHERE b.guest_id = %s AND b.status != 'canceled'
            ORDER BY e.event_datetime DESC
        """, (user_id,))

        if not bookings:
            ctk.CTkLabel(scrollable_frame, text="No active bookings found",
                         font=FONTS['medium'], text_color=COLORS['primary']).pack(pady=40)
            return

        current_time = datetime.now()
        for book in bookings:
            # Stylish card with shadow effect
            event_frame = ctk.CTkFrame(scrollable_frame, 
                                     fg_color=COLORS['card_background'], 
                                     corner_radius=15,
                                     border_width=1,
                                     border_color=COLORS['border'])
            event_frame.pack(pady=15, padx=20, fill='x')

            event_time = book['event_datetime'] if isinstance(book['event_datetime'], datetime) \
                else datetime.strptime(book['event_datetime'], "%Y-%m-%d %H:%M:%S")
            is_past = event_time < current_time

            # Content container with padding
            content_frame = ctk.CTkFrame(event_frame, fg_color="transparent")
            content_frame.pack(expand=True, fill='both', padx=15, pady=15)

            # Status badge
            status_frame = ctk.CTkFrame(content_frame, 
                                      fg_color=COLORS['secondary'] if not is_past else COLORS['disabled'],
                                      corner_radius=8)
            status_frame.pack(anchor='ne', pady=5)
            status_text = "PAST EVENT" if is_past else "UPCOMING"
            ctk.CTkLabel(status_frame, text=status_text,
                        font=FONTS['small_bold'], text_color="white").pack(padx=10, pady=3)

            # Two-column layout
            left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
            left_column.pack(side='left', fill='both', expand=True)

            right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
            right_column.pack(side='right', padx=10)

            # Event title
            ctk.CTkLabel(left_column, text=book['event_name'].upper(),
                        font=FONTS['large_bold'], text_color=COLORS['primary']).pack(anchor='w', pady=(0, 10))

            # Event details in a grid
            details_frame = ctk.CTkFrame(left_column, fg_color="transparent")
            details_frame.pack(fill='x', pady=5)

            details = [
                (f"🗓  {event_time.strftime('%d %B %Y, %I:%M %p')}", FONTS['medium']),
                (f"📍  {book['address']}", FONTS['medium']),
                (f"👨‍🍳  Host: {book['host_name']}", FONTS['medium']),
                (f"👥  Attendees: {book['number_of_attendees']}", FONTS['medium']),
                (f"💰  Paid Amount: ${book['paid_amount']:.2f}", FONTS['medium_bold']),
                (f"📅  Booked on: {book['booking_time'].strftime('%d %B %Y %I:%M %p')}", FONTS['medium']),
            ]

            for text, font in details:
                ctk.CTkLabel(details_frame, text=text, font=font, text_color=COLORS['primary']).pack(anchor='w', pady=3)

            # Controls column
            controls_frame = ctk.CTkFrame(right_column, fg_color="transparent")
            controls_frame.pack(pady=20)

            if not is_past:
                ctk.CTkButton(controls_frame, text="Edit",
                             command=lambda bid=book['booking_id'], eid=book['event_id'], 
                             op=book['number_of_attendees'], mc=book['total_capacity'], cf=controls_frame: 
                             edit_booking(bid, eid, op, mc, cf),
                             **STYLES['accent_button']).pack(pady=5)
                ctk.CTkButton(controls_frame, text="Cancel",
                             command=lambda bid=book['booking_id'], eid=book['event_id'], 
                             np=book['number_of_attendees']: cancel_booking(bid, eid, np),
                             **STYLES['danger_button']).pack(pady=5)
            else:
                ctk.CTkLabel(controls_frame, text="EVENT ENDED",
                            font=FONTS['medium'], text_color=COLORS['disabled']).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load bookings: {str(e)}")

# ================== NAVIGATION FUNCTIONS ==================
def show_profile():
    subprocess.Popen(['python3', 'guest_dashboard.py', user_id])
    window.destroy()

def open_search_events():
    subprocess.Popen(['python3', 'search_events.py', user_id])
    window.destroy()

def open_view_bookings():
    subprocess.Popen(['python3', 'my_bookings.py', user_id, 'guest'])
    window.destroy()

def open_feedback():
    subprocess.Popen(['python3', 'provide_feedback.py', user_id])
    window.destroy()

def logout():
    subprocess.Popen(['python3', 'login.py'])
    window.destroy()

# ================== UI SETUP ==================
window = ctk.CTk()
window.title("Guest Dashboard")
window.geometry("1000x720")
window.configure(fg_color=COLORS['background'])

user_id = sys.argv[1] if len(sys.argv) > 1 else None
if not user_id:
    messagebox.showerror("Error", "User ID missing")
    sys.exit(1)

# Header
header_frame = create_styled_frame(window)
header_frame.pack(padx=20, pady=(20, 10), fill='x')

header_label = ctk.CTkLabel(header_frame, text="🍽 Guest Dashboard",
                            font=FONTS['header'], text_color=COLORS['primary'])
header_label.pack(pady=10)

# Navigation Bar
nav_frame = ctk.CTkFrame(header_frame, fg_color=COLORS['navbar'], corner_radius=10)
nav_frame.pack(fill='x', padx=10, pady=5)

for (label, action) in [
    ("Profile", show_profile),
    ("Search Events", open_search_events),
    ("My Bookings", open_view_bookings),
    ("Feedback", open_feedback),
    ("Logout", logout)
]:
    ctk.CTkButton(nav_frame, text=label, command=action, width=120,
                  fg_color=COLORS['accent'], hover_color=COLORS['accent_dark'],
                  text_color="white", font=FONTS['small']).pack(side='left', padx=10, pady=5)

# Scrollable Booking Area
main_frame = create_styled_frame(window)
main_frame.pack(pady=(10, 20), padx=20, fill='both', expand=True)

canvas = ctk.CTkCanvas(main_frame, bg=COLORS['background'], highlightthickness=0)
scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=canvas.yview)
scrollable_frame = ctk.CTkFrame(canvas, fg_color=COLORS['background'])

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

load_bookings()
window.mainloop()