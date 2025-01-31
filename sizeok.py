import sqlite3
from tkinter import *
from tkinter.filedialog import askopenfilename
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from tkinter import PhotoImage
from reportlab.platypus import SimpleDocTemplate, Paragraph,Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import os
import webbrowser

# Database Connection
try:
    with sqlite3.connect('library.db') as connector:
        cursor = connector.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Library (
                BK_NAME TEXT, 
                BK_ID TEXT PRIMARY KEY NOT NULL, 
                AUTHOR_NAME TEXT, 
                BK_STATUS TEXT, 
                CARD_ID TEXT,
                DATE_ADDED TEXT,
                DATE_ISSUED TEXT,  
                DATE_RETURNED TEXT)
        ''')

        cursor.execute('CREATE TABLE IF NOT EXISTS Users (USERNAME TEXT PRIMARY KEY NOT NULL, PASSWORD TEXT, ROLE TEXT)')

except sqlite3.Error as e:
    print("SQLite error:", e)
    # Handle the error as appropriate

# GUI
root = Tk()
root.title('Library Management System')
root.attributes('-fullscreen', True)  # Set fullscreen
root.configure(bg='white')

# Variables
lf_bg = 'LightYellow4'
rtf_bg = 'white'
rbf_bg = 'cadet blue'
btn_hlb_bg = 'burlywood3'

lbl_font = ('Georgia', 13)
entry_font = ('Times New Roman', 12)
btn_font = ('Gill Sans MT', 13)

bk_status = StringVar()
bk_name = StringVar()
bk_id = StringVar()
author_name = StringVar()
card_id = StringVar()

# Frames
left_frame = Frame(root, bg=lf_bg)
left_frame.place(relx=0, rely=0, relwidth=0.3, relheight=1)

RT_frame = Frame(root, bg=rtf_bg)
RT_frame.place(relx=0.3, rely=0, relwidth=0.7, relheight=0.2)

RB_frame = Frame(root)
RB_frame.place(relx=0.3, rely=0.2, relwidth=0.7, relheight=0.8)
# GUI


def generate_receipt(book_name, book_id, card_id, issuance_date):
    filename = "receipt.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    receipt_content = []
    receipt_content.append(Paragraph("Receipt for Book Issuance", styles["Title"]))
    receipt_content.append(Paragraph(f"Book Name: {book_name}", styles["Normal"]))
    receipt_content.append(Paragraph(f"Book ID: {book_id}", styles["Normal"]))
    receipt_content.append(Paragraph(f"Borrower's Card ID: {card_id}", styles["Normal"]))
    receipt_content.append(Paragraph(f"Issuance Date: {issuance_date}", styles["Normal"]))

    doc.build(receipt_content)
    
    # Open the file using default PDF viewer
    webbrowser.open(os.path.abspath(filename))

def issue_book():
    global tree, connector

    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    bk_id = values['values'][1]
    bk_status = values["values"][3]

    if bk_status == 'Available':
        card_id = sd.askstring('Borrower Card ID', 'Enter the Card ID of the borrower:')
        if validate_card_id(card_id):
            issuance_date = str(datetime.now())
            cursor.execute('UPDATE Library SET bk_status=?, card_id=?, DATE_ISSUED=? WHERE bk_id=?',
                           ('Issued', card_id, issuance_date, bk_id))
            connector.commit()
            mb.showinfo('Book Issued', 'The book has been issued to the borrower with Card ID ' + card_id)
            # Generate receipt
            generate_receipt(values['values'][0], values['values'][1], card_id, issuance_date)
        else:
            mb.showinfo('Issue Canceled', 'Book issue operation canceled.')
    else:
        mb.showinfo('Book Not Available', 'The selected book is not available for issuing.')

    clear_and_display()

def return_book():
    global tree, connector

    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return


def return_book():
    global tree, connector

    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    BK_id = values['values'][1]
    BK_status = values["values"][3]

    if BK_status == 'Issued':
        surety = mb.askyesno('Is return confirmed?', 'Has the book been returned by the borrower?')
        if surety:
            return_date = datetime.now()
            expected_return_date = datetime.strptime(values['values'][6], '%Y-%m-%d %H:%M:%S.%f')  # Convert string to datetime
            days_late = (return_date - expected_return_date).days
            fine = max(0, days_late)  # Calculate fine (1 rupee per day), ensure it's not negative
            fine_amount = fine * 1  # Fine per day is 1 rupee
            mb.showinfo('Fine Calculation', f'The book has been returned successfully.\nFine: {fine_amount} rupees')
            
            # Update database with return date and status
            cursor.execute('UPDATE Library SET bk_status=?, card_id=?, DATE_RETURNED=? WHERE bk_id=?',
                           ('Available', 'N/A', str(return_date), BK_id))
            connector.commit()
        else:
            mb.showinfo('Return Canceled', 'Book return operation canceled.')
    else:
        mb.showinfo('Book Not Issued', 'The selected book has not been issued and cannot be returned.')

    clear_and_display()

def validate_card_id(card_id):
    if not card_id:
        mb.showerror('Invalid Card ID', 'Card ID cannot be empty.')
        return False
    if len(card_id) != 9 or not card_id.isalnum():
        mb.showerror('Invalid Card ID', 'Card ID must be 9 characters long and contain only alphanumeric characters.')
        return False

    return True


def search_books():
    query = search_entry.get().strip()
    if query:
        cursor.execute('''
            SELECT * FROM Library 
            WHERE BK_NAME LIKE ? OR AUTHOR_NAME LIKE ? OR BK_ID LIKE ?
        ''', ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        data = cursor.fetchall()

        if data:
            display_records(tree, data)
        else:
            mb.showinfo('Search Results', 'No matching records found.')
    else:
        mb.showwarning('Empty Query', 'Please enter a search query.')


def sort_books(column):
    # Map user-friendly column names to actual column names in the table
    column_mapping = {'Book Name': 'BK_NAME', 'Author': 'AUTHOR_NAME', 'Book ID': 'BK_ID', 'Status': 'BK_STATUS'}
    actual_column = column_mapping.get(column, column)

    cursor.execute(f'SELECT * FROM Library ORDER BY {actual_column}')
    data = cursor.fetchall()
    display_records(tree, data)


def filter_books(status):
    cursor.execute('SELECT * FROM Library WHERE BK_STATUS=?', (status,))
    data = cursor.fetchall()
    display_records(tree, data)

def export_data():
    # Get data from the database
    cursor.execute('SELECT * FROM Library')
    data = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    # Create PDF document
    pdf_filename = 'library_inventory.pdf'
    doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(letter))  # Set landscape orientation
    elements = []

    # Create table
    table_data = [headers] + data
    table = Table(table_data, colWidths=[100, 100, 100, 100, 100, 100, 100, 100])  # Adjust column widths as needed

    # Define style for table
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    table.setStyle(style)

    # Add table to elements list
    elements.append(table)

    # Build PDF document
    doc.build(elements)

    mb.showinfo('Export Successful', f'Library inventory data exported to {pdf_filename}')

def import_data():
    mb.showinfo('Feature Coming Soon', 'This feature is under development.')

def change_availability():
    global card_id, tree, connector

    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    BK_id = values['values'][1]
    BK_status = values["values"][3]

    if BK_status == 'Issued':
        surety = mb.askyesno('Is return confirmed?', 'Has the book been returned to you?')
        if surety:
            cursor.execute('UPDATE Library SET bk_status=?, card_id=?, DATE_RETURNED=? WHERE bk_id=?',
                           ('Available', 'N/A', str(datetime.now()), BK_id))
            connector.commit()
    else:
        mb.showinfo('Cannot be returned', 'The book status cannot be set to Available unless it has been returned')
        cursor.execute('UPDATE Library SET bk_status=?, card_id=?, DATE_ISSUED=? WHERE bk_id=?',
                       ('Issued', issuer_card(), str(datetime.now()), BK_id))
        connector.commit()

    clear_and_display()


def issuer_card():
    Cid = sd.askstring('Issuer Card ID', 'What is the Issuer\'s Card ID?\t\t\t')

    if not Cid:
        mb.showerror('Issuer ID cannot be zero!', 'Can\'t keep Issuer ID empty, it must have a value')
    else:
        return Cid


def display_records(tree, data):
    tree.delete(*tree.get_children())
    for records in data:
        tree.insert('', END, values=records)


def clear_fields():
    global bk_status, bk_id, bk_name, author_name, card_id, tree

    bk_status.set('Available')

    for i in [bk_id, bk_name, author_name, card_id]:
        i.set('')

    bk_id_entry.config(state='normal')

    try:
        if tree.selection():
            tree.selection_remove(tree.selection()[0])
    except IndexError:
        pass


def clear_and_display():
    global bk_status, bk_id, bk_name, author_name, card_id, tree

    try:
        if root and root.winfo_exists():
            bk_status.set('Available')

            for i in [bk_id, bk_name, author_name, card_id]:
                i.set('')

            bk_id_entry.config(state='normal')

            if tree and tree.winfo_exists():
                try:
                    if tree.selection():
                        tree.selection_remove(tree.selection()[0])
                except IndexError:
                    pass

            cursor.execute('SELECT * FROM Library')
            data = cursor.fetchall()
            display_records(tree, data)

            root.update()
    except Exception as e:
        # Handle the exception, e.g., print an error message
        print("An error occurred while clearing and displaying:", e)


def view_record():
    global bk_name, bk_id, bk_status, author_name, tree

    if not tree.focus():
        mb.showerror('Select a row!',
                     'To view a record, you must select it in the table. Please do so before continuing.')
        return

    current_item_selected = tree.focus()
    values_in_selected_item = tree.item(current_item_selected)
    selection = values_in_selected_item['values']

    bk_name.set(selection[0])
    bk_id.set(selection[1])
    bk_status.set(selection[3])
    author_name.set(selection[2])


def add_record():
    global connector, bk_name, bk_id, author_name, bk_status, card_id

    if bk_status.get() == 'Issued':
        card_id.set(issuer_card())
    else:
        card_id.set('N/A')

    surety = mb.askyesno('Are you sure?',
                         'Are you sure this is the data you want to enter?\nPlease note that Book ID cannot be changed in the future')

    if surety:
        try:
            connector.execute(
                'INSERT INTO Library (BK_NAME, BK_ID, AUTHOR_NAME, BK_STATUS, CARD_ID) VALUES (?, ?, ?, ?, ?)',
                (bk_name.get(), bk_id.get(), author_name.get(), bk_status.get(), card_id.get()))
            connector.commit()

            clear_and_display()

            mb.showinfo('Record added', 'The new record was successfully added to your database')
        except sqlite3.IntegrityError:
            mb.showerror('Book ID already in use!',
                         'The Book ID you are trying to enter is already in the database, please alter that book\'s record or check any discrepancies on your side')


def update_record():
    def update_record():
        def update():
            global bk_status, bk_name, bk_id, author_name, card_id
            global connector, tree

            if bk_status.get() == 'Issued':
                card_id.set(issuer_card())
            else:
                card_id.set('N/A')

            cursor.execute('UPDATE Library SET BK_NAME=?, BK_STATUS=?, AUTHOR_NAME=?, CARD_ID=? WHERE BK_ID=?',
                           (bk_name.get(), bk_status.get(), author_name.get(), card_id.get(), bk_id.get()))
            connector.commit()

            clear_and_display()

            edit.destroy()
            bk_id_entry.config(state='normal')
            clear.config(state='normal')

        view_record()

        bk_id_entry.config(state='disabled')  # Fix the method name here
        clear.config(state='disabled')

        edit = Button(left_frame, text='Update Record', font=btn_font, bg=btn_hlb_bg, width=20, command=update)
        edit.place(x=50, y=375)


def remove_record():
    if not tree.selection():
        mb.showerror('Error!', 'Please select an item from the database')
        return

    current_item = tree.focus()
    values = tree.item(current_item)
    selection = values["values"]

    cursor.execute('DELETE FROM Library WHERE BK_ID=?', (selection[1],))
    connector.commit()

    tree.delete(current_item)

    mb.showinfo('Done', 'The record you wanted deleted was successfully deleted.')

    clear_and_display()


def delete_inventory():
    if mb.askyesno('Are you sure?',
                   'Are you sure you want to delete the entire inventory?\n\nThis command cannot be reversed'):
        tree.delete(*tree.get_children())

        cursor.execute('DELETE FROM Library')
        connector.commit()
    else:
        return
def generate_report():
    cursor.execute("SELECT COUNT(*) FROM Library WHERE BK_STATUS='Issued'")
    total_borrowed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Library WHERE BK_STATUS='Available'")
    total_available = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Library WHERE DATE_RETURNED IS NOT NULL")
    total_returned = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Library WHERE DATE_ISSUED < DATE_RETURNED OR DATE_RETURNED IS NULL")
    total_overdue = cursor.fetchone()[0]

    report_text = f"Total Books Borrowed: {total_borrowed}\nTotal Books Available: {total_available}\nTotal Books Returned: {total_returned}\nTotal Books Overdue: {total_overdue}"

    mb.showinfo('Library Statistics', report_text)

# Additional Buttons

search_entry = Entry(root, font=entry_font)
search_entry.place(x=750, y=610)
search_button = Button(root, text='Search', font=btn_font, bg=btn_hlb_bg, width=12, command=search_books)
search_button.place(x=900, y=600)

export_button = Button(root, text='Export Data', font=btn_font, bg=btn_hlb_bg, width=12, command=export_data)
export_button.place(x=900, y=100)

import_button = Button(root, text='Import Data', font=btn_font, bg=btn_hlb_bg, width=12, command=import_data)
import_button.place(x=1023, y=100)


# Sort and Filter Buttons
sort_label = Label(root, text='Sort By:', bg=lf_bg, font=lbl_font)
sort_label.place(x=440, y=610)

sort_options = ttk.Combobox(root, values=('Book Name', 'Author', 'Book ID', 'Status'))
sort_options.place(x=500, y=610)
sort_options.set('Book Name')

sort_button = Button(root, text='Sort', font=btn_font, bg=btn_hlb_bg, width=10,
                     command=lambda: sort_books(sort_options.get().replace(' ', '_').upper()))
sort_button.place(x=650, y=605)

filter_label = Label(root, text='Filter By:', bg=lf_bg, font=lbl_font)
filter_label.place(x=440, y=650)

filter_options = ttk.Combobox(root, values=('Available', 'Issued'))
filter_options.place(x=500, y=650)
filter_options.set('Available')

filter_button = Button(root, text='Filter', font=btn_font, bg=btn_hlb_bg, width=10,
                       command=lambda: filter_books(filter_options.get()))
filter_button.place(x=650, y=645)

# Left Frame
Label(left_frame, text='Book Name', bg=lf_bg, font=lbl_font).place(x=98, y=25)
Entry(left_frame, width=25, font=entry_font, textvariable=bk_name).place(x=45, y=55)

Label(left_frame, text='Book ID', bg=lf_bg, font=lbl_font).place(x=110, y=105)
bk_id_entry = Entry(left_frame, width=25, font=entry_font, textvariable=bk_id)
bk_id_entry.place(x=45, y=135)

Label(left_frame, text='Author Name', bg=lf_bg, font=lbl_font).place(x=90, y=185)
Entry(left_frame, width=25, font=entry_font, textvariable=author_name).place(x=45, y=215)

Label(left_frame, text='Status of the Book', bg=lf_bg, font=lbl_font).place(x=75, y=265)
dd = OptionMenu(left_frame, bk_status, *['Available', 'Issued'])
dd.configure(font=entry_font, width=12)
dd.place(x=75, y=300)

submit = Button(left_frame, text='Add new record', font=btn_font, bg=btn_hlb_bg, width=20, command=add_record)
submit.place(x=50, y=375)

clear = Button(left_frame, text='Clear fields', font=btn_font, bg=btn_hlb_bg, width=20, command=clear_fields)
clear.place(x=50, y=435)

# Right Top Frame
logo_img = PhotoImage(file="lmsbk.png")
logo_label = Label(RT_frame, image=logo_img, bg='skyblue1')
logo_label.place(x=10, y=10)
Button(RT_frame, text='Delete book record', font=btn_font, bg=btn_hlb_bg, width=17, command=remove_record).place(x=8,
                                                                                                                 y=100)
Button(RT_frame, text='Delete full inventory', font=btn_font, bg=btn_hlb_bg, width=17, command=delete_inventory).place(
    x=178, y=100)
Button(RT_frame, text='Update book details', font=btn_font, bg=btn_hlb_bg, width=17, command=update_record).place(x=348,
                                                                                                                  y=100)
# Availability Change Button
change_availability_button = Button(root, text='Change Availability', font=btn_font, bg=btn_hlb_bg, width=20,
                                    command=change_availability)
change_availability_button.place(x=750, y=645)

# Right Bottom Frame
Label(RB_frame, text='BOOK INVENTORY', bg=rbf_bg, font=("Noto Sans CJK TC", 15, 'bold')).pack(side=TOP, fill=X)

tree = ttk.Treeview(RB_frame, selectmode=BROWSE, columns=('Book Name', 'Book ID', 'Author', 'Status', 'Issuer Card ID'))

XScrollbar = Scrollbar(tree, orient=HORIZONTAL, command=tree.xview)
YScrollbar = Scrollbar(tree, orient=VERTICAL, command=tree.yview)
XScrollbar.pack(side=BOTTOM, fill=X)
YScrollbar.pack(side=RIGHT, fill=Y)

tree.config(xscrollcommand=XScrollbar.set, yscrollcommand=YScrollbar.set)

tree.heading('Book Name', text='Book Name', anchor=CENTER)
tree.heading('Book ID', text='Book ID', anchor=CENTER)
tree.heading('Author', text='Author', anchor=CENTER)
tree.heading('Status', text='Status of the Book', anchor=CENTER)
tree.heading('Issuer Card ID', text='Card ID of the Issuer', anchor=CENTER)

tree.column('#0', width=0, stretch=NO)
tree.column('#1', width=225, stretch=NO)
tree.column('#2', width=70, stretch=NO)
tree.column('#3', width=150, stretch=NO)
tree.column('#4', width=105, stretch=NO)
tree.column('#5', width=132, stretch=NO)

tree.place(y=30, x=0, relheight=0.9, relwidth=1)

# Buttons for issuing and returning books
issue_button = Button(root, text='Issue Book', font=btn_font, bg=btn_hlb_bg, width=20, command=issue_book)
issue_button.place(x=50, y=495)

return_button = Button(root, text='Return Book', font=btn_font, bg=btn_hlb_bg, width=20, command=return_book)
return_button.place(x=50, y=550)
report_button = Button(root, text='Generate Report', font=btn_font, bg=btn_hlb_bg, width=20, command=generate_report)
report_button.place(x=50, y=605)    

clear_and_display()
# Mainloop
root.mainloop()
