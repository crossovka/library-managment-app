import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from datetime import datetime, timedelta
import mysql.connector
# Подключение к базе данных
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="Библиотека"
)
mycursor = mydb.cursor()
def get_table_names():
    mycursor.execute("SHOW TABLES")
    return [table[0] for table in mycursor.fetchall()]
def view_records(table_name):
    mycursor.execute(f"SELECT * FROM {table_name}")
    records = mycursor.fetchall()
    return records
def get_column_names(table_name):
    mycursor.execute(f"DESCRIBE {table_name}")
    return [column[0] for column in mycursor.fetchall()]
def get_primary_key_column(table_name):
    try:
        mycursor.execute(f"SHOW KEYS FROM `{table_name}` WHERE Key_name = 'PRIMARY'")
        result = mycursor.fetchone()
        if result:
            return result[4]
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"An error occurred: {err}")
    return None
def insert_record(table_name, values):
    columns = ', '.join(get_column_names(table_name))
    placeholders = ', '.join(['%s'] * len(values))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    mycursor.execute(query, values)
    mydb.commit()
def update_record(table_name, primary_key_column, values, primary_key_value):
    columns = get_column_names(table_name)
    columns.remove(primary_key_column)
    updates = ', '.join([f"`{column}` = %s" for column in columns])
    query = f"UPDATE `{table_name}` SET {updates} WHERE `{primary_key_column}` = %s"
    mycursor.execute(query, values + (primary_key_value,))
    mydb.commit()
def delete_record(table_name, primary_key_name, record_id):
    try:
        query = f"DELETE FROM `{table_name}` WHERE `{primary_key_name}` = %s"
        mycursor.execute(query, (record_id,))
        mydb.commit()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"An error occurred: {err}")
root = tk.Tk()
root.title("Управление библиотекой")
table_listbox = tk.Listbox(root)
table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
def populate_table_list():
    table_listbox.delete(0, tk.END)
    tables = get_table_names()
    for table in tables:
        table_listbox.insert(tk.END, table)
populate_table_list()
records_frame = ttk.Frame(root)
records_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
records_treeview = ttk.Treeview(records_frame)
records_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
def show_records(event):
    # Clear existing records in treeview
    for record in records_treeview.get_children():
        records_treeview.delete(record)
    selected_table = table_listbox.get(tk.ANCHOR)
    records = view_records(selected_table)
    if records:
        columns = get_column_names(selected_table)
        records_treeview["columns"] = columns
        for col in columns:
            records_treeview.heading(col, text=col)
        for record in records:
            records_treeview.insert("", tk.END, values=record)
table_listbox.bind("<<ListboxSelect>>", show_records)
def add_record():
    selected_table = table_listbox.get(tk.ANCHOR)
    columns = get_column_names(selected_table)
    input_values = []
    for col in columns:
        input_values.append(simpledialog.askstring("Ввод", f"Введите значение для {col}:"))
    insert_record(selected_table, tuple(input_values))
    show_records(None)
add_button = tk.Button(root, text="Добавить запись", command=add_record)
add_button.pack(side=tk.BOTTOM)
def update_record_dialog():
    selected_table = table_listbox.get(tk.ANCHOR)
    primary_key_name = get_primary_key_column(selected_table)
    if primary_key_name is None:
        messagebox.showerror("Error", f"Could not find primary key for {selected_table}")
        return
    record_id = simpledialog.askinteger("Input", f"Enter {primary_key_name} of the record to update:")
    if record_id is None:
        return
    columns = get_column_names(selected_table)
    input_values = []
    primary_key_index = columns.index(primary_key_name)
    query = f"SELECT * FROM {selected_table} WHERE {primary_key_name} = %s"
    mycursor.execute(query, (record_id,))
    current_values = mycursor.fetchone()
    if not current_values:
        messagebox.showerror("Error", f"No record found with {primary_key_name} = {record_id}")
        return
    for i, col in enumerate(columns):
        if i != primary_key_index:
            current_value = current_values[i]
            new_val = simpledialog.askstring("Input", f"Current value for {col}: {current_value}\nEnter new value for {col}:")
            input_values.append(new_val if new_val != "" else current_value)
    update_record(selected_table, primary_key_name, tuple(input_values), record_id)
    show_records(None)
update_button = tk.Button(root, text="Обновить запись", command=update_record_dialog)
update_button.pack(side=tk.BOTTOM)
def calculate_rent():
    selected_table = "ИсторияВыдачи"
    record_id = simpledialog.askinteger("Ввод", "Введите ID записи истории выдачи для расчета стоимости проката:")
    if record_id is not None:
        query = f"SELECT КодКниги, ДатаВыдачи, ДатаВозврата FROM {selected_table} WHERE КодВыдачи = %s"
        mycursor.execute(query, (record_id,))
        lending_info = mycursor.fetchone()
        if lending_info:
            book_id, start_date, end_date = lending_info
            end_date = datetime.strptime(end_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
            start_date = datetime.combine(start_date, datetime.min.time())
            rent_days = (end_date - start_date).days
            if rent_days <= 0:
                messagebox.showerror("Ошибка", "Некорректные даты выдачи: дата возврата должна быть после даты выдачи")
                return
            query = f"SELECT СтоимостьПроката FROM Книги WHERE КодКниги = %s"
            mycursor.execute(query, (book_id,))
            rent_cost = mycursor.fetchone()
            if rent_cost:
                rent_cost = rent_cost[0]
                total_rent_cost = rent_cost * rent_days
                messagebox.showinfo("Стоимость проката", f"Общая стоимость проката для записи истории выдачи с ID {record_id} составляет {total_rent_cost} единиц")
            else:
                messagebox.showerror("Ошибка", f"Книга с ID {book_id} не найдена в таблице 'Книги'")
        else:
            messagebox.showerror("Ошибка", f"Запись истории выдачи с ID {record_id} не найдена")
calculate_button = tk.Button(root, text="Рассчитать стоимость проката", command=calculate_rent)
calculate_button.pack(side=tk.BOTTOM)
def delete_record_dialog():
    selected_table = table_listbox.get(tk.ANCHOR)
    primary_key_name = get_primary_key_column(selected_table)
    if primary_key_name is None:
        messagebox.showerror("Error", f"Could not find primary key for {selected_table}")
        return
    record_id = simpledialog.askinteger("Input", f"Enter {primary_key_name} of the record to delete:")
    if record_id is not None:
        delete_record(selected_table, primary_key_name, record_id)
        show_records(None)
delete_button = tk.Button(root, text="Удалить запись", command=delete_record_dialog)
delete_button.pack(side=tk.BOTTOM)
root.mainloop()