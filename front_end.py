from tkinter import *
from mysql.connector import Error
from backend import Data


def connect():
    Data(ip_text.get())
    if Data.server:
        T1.config(state='normal')
        T1.delete('1.0', END)
        T1.insert(END, Data.conn_status)
        T1.insert(END, Data.conn_to)
        T1.config(state='disabled')
    else:
        T1.config(state='normal')
        T1.delete('1.0', END)
        T1.insert(END, Data.err)
        T1.config(state='disabled')


class DataButtons:

    def __init__(self, file):
        self.file = file
        if Data.server:
            self.sql = Data.format_script(self.file, date_text.get())
            try:
                Data.query(self.sql)
            except Error as e:
                T1.config(state='normal')
                T1.delete('1.0', END)
                T1.insert(END, e)
                T1.config(state='disabled')
        else:
            T1.config(state='normal')
            T1.delete('1.0', END)
            T1.insert(END, 'You are not connected to any DB')


b1_file = 'all_inv.sql'
b2_file = 'inv_target_month.sql'
b3_file = 'never_inv.sql'
b4_file = 'not_inv_target_month.sql'


def data_one():
    DataButtons(b1_file)
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, 'Extraction complete')


def data_two():
    DataButtons(b2_file)
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, 'Extraction complete')


def data_three():
    DataButtons(b3_file)
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, 'Extraction complete')


def data_four():
    DataButtons(b4_file)
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, 'Extraction complete')


window = Tk()

l1 = Label(window, text='Month')
l1.grid(row=0, column=0, pady=(20, 0), padx=(20, 5))

l2 = Label(window, text='IP')
l2.grid(row=1, column=0, pady=(0, 20), padx=(20, 5))

date_text = StringVar()
e1 = Entry(window, textvariable=date_text)
e1.grid(row=0, column=1, pady=(20, 0), padx=(0, 20))

ip_text = StringVar()
e1 = Entry(window, textvariable=ip_text)
e1.grid(row=1, column=1, pady=(0, 20), padx=(0, 20))

T1 = Text(window, height=10, width=30)
T1.grid(row=2, column=0, rowspan=8, columnspan=1, pady=(0, 0), padx=(20, 5))
T1.config(state='disabled')

b1 = Button(window, text='data 1', width=15, command=data_one)
b1.grid(row=2, column=1, pady=(0, 10), padx=(0, 8))

b2 = Button(window, text='data 2', width=15)
b2.grid(row=3, column=1, pady=(0, 10), padx=(0, 8))

b3 = Button(window, text='data 3', width=15)
b3.grid(row=4, column=1, pady=(0, 10), padx=(0, 8))

b4 = Button(window, text='data 4', width=15)
b4.grid(row=5, column=1, pady=(0, 10), padx=(0, 8))

b5 = Button(window, text='all data', width=15)
b5.grid(row=6, column=1, pady=(0, 10), padx=(0, 8))

b6 = Button(window, text='view data', width=15)
b6.grid(row=7, column=1, pady=(0, 10), padx=(0, 8))

b7 = Button(window, text='email data', width=15)
b7.grid(row=8, column=1, pady=(0, 10), padx=(0, 8))

b8 = Button(window, text='close', width=15, command=window.destroy)
b8.grid(row=8, column=1, pady=(0, 10), padx=(0, 8))

window.mainloop()
