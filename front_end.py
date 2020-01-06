import os
import select
import socket
from configparser import RawConfigParser
from tkinter import *
from _email import EmailApi

import pandas as pd
import paramiko


class MySqlScriptError(Exception):
    """Exception class that is raised when stderr is not empty"""

    def __init__(self, stderr):
        Exception.__init__(self)
        self.errorMsg = stderr

    def __str__(self):
        return t_insert(f"--- MySqlScriptError ---\n{self.errorMsg}")

    def __repr__(self): return self.__str__()


class SshUtility:
    """'this class contains methods that will be used for interacting with the remote server"""

    def __init__(self):
        self.client = None
        self.stdout_chunks = None
        self.stderr_chunks = None
        self.local_target = None
        self.password = password
        self.username = username

    def server_connect(self):

        """'Establishes connection to the remote server"""

        t_insert('Setting up SSH Connection...\n')
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=ip_text.get(), username=username, password=password)
            T1.config(state='normal')
            T1.insert(END, '\nSuccessfully Connected!')
            T1.config(state='disabled')
        except socket.timeout as e:
            t_insert(e)
            self.client.close()
            raise
        except paramiko.AuthenticationException as e:
            t_insert(e)
            self.client.close()
            raise
        except paramiko.SSHException as e:
            t_insert(e)
            self.client.close()
            raise
        except Exception as e:
            t_insert(e)
            self.client.close()
            raise

    def exec_cmd(self, cmd):

        """executes desired command on remote server"""

        try:
            if self.server_connect:
                timeout = 10
                t_insert('Executing Command...')
                stdin, stdout, stderr = self.client.exec_command(cmd)
                channel = stdout.channel
                stdin.close()
                channel.shutdown_write()

                self.stderr_chunks = []
                self.stdout_chunks = []

                while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
                    # stop if channel was closed prematurely, and there is no data in the buffers.
                    got_chunk = False
                    read_q, _, _ = select.select([stdout.channel], [], [], timeout)
                    if read_q:
                        for com in read_q:
                            if com.recv_ready():
                                # reads stdout and append result to stdout_chunks
                                self.stdout_chunks.append(stdout.channel.recv(len(com.in_buffer)).decode())
                                got_chunk = True
                            if com.recv_stderr_ready():
                                # reads stderr and append result to stderr_chunks
                                self.stderr_chunks.append(
                                    stderr.channel.recv_stderr(len(com.in_stderr_buffer)).decode())
                                got_chunk = True
                    else:
                        continue

                    if not got_chunk \
                            and stdout.channel.exit_status_ready() \
                            and not stderr.channel.recv_stderr_ready() \
                            and not stdout.channel.recv_ready():
                        # if the above conditions are met, implies that there is no more data to be read
                        stdout.channel.shutdown_read()
                        stdout.channel.close()
                        break  # exit as remote side is finished and our buffers are empty

                stdout.close()
                stderr.close()

                exit_code = stdout.channel.recv_exit_status()
                # most 'good' servers will return an exit code after executing a command
                if self.stdout_chunks and exit_code == 0:  # exit code zero usually implies no errors occurred
                    return t_insert(f"SQL query completed!..\n\n{''.join(self.stdout_chunks)}")

                if self.stdout_chunks and exit_code != 0:
                    # exit code zero returned, but stderr is not empty, this could imply minor issues or warnings
                    return t_insert(f"SQL query completed..\n\nWarning:\n\n{''.join(self.stdout_chunks)}")

                if len(self.stderr_chunks) > 0:  # non-zero exit code implies error
                    raise (MySqlScriptError(self.stderr_chunks))  # raises the MySqlScriptError class
            else:
                t_insert('Please Establish a connection...')
        except paramiko.SSHException as e:
            t_insert(e)
            self.client.close()
            raise
        except Exception as e:
            t_insert(e)
            self.client.close()
            raise

    def file_copy(self, file_name):

        """copies target file from remote server. note that this method can be implemented using the get() method
        of paramiko sftp. but"""

        dest_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        if not os.path.exists(f'{dest_path}\\data_extract'):
            os.mkdir(f'{dest_path}\\data_extract')

        self.local_target = f'{dest_path}\\data_extract'
        remote_target = f'/var/lib/mysql-files/{file_name}'
        try:
            if self.server_connect:
                sftp = self.client.open_sftp()
                T1.config(state='normal')
                T1.delete('1.0', END)
                T1.insert(END, 'Copying data from server to LocalHost...\n')
                with sftp.file(remote_target, 'r') as remote:
                    with open(f"{self.local_target}\\{file_name}", "w+") as local:
                        for lines in remote:
                            local.write(lines)
                T1.insert(END, 'Data transfer complete...')
                T1.config(state='disabled')
            else:
                t_insert('---Connection lost---')
        except paramiko.SSHException as e:
            t_insert(e)
            self.client.close()
            raise
        except Exception as e:
            t_insert(e)
            self.client.close()
            raise

    def data_clean(self, target_data):

        """clean and transform data"""

        T1.config(state='normal')
        T1.delete('1.0', END)
        T1.insert(END, 'Transforming data...\n')
        output_name = target_data.split('.')[0]
        data = pd.read_csv(f'{self.local_target}\\{target_data}', header=None, index_col=False)
        if len(data.columns) == 8:
            data.columns = ['TPIN', 'Tax_Payername', 'Terminal_ID', 'Taxpayer_Address', 'Tax_Office', 'Latest_Time',
                            'Issued', 'Sector']
        else:
            data.columns = ['TPIN', 'Tax_Payerame', 'Terminal_ID', 'Taxpayer_Address', 'Tax_Office', 'Latest_Time',
                            'Issued', 'Total_Sales', 'Total_Tax', 'Sector']
        data.TPIN = data.TPIN.astype(str)
        data.Terminal_ID = data.Terminal_ID.astype(str)
        data.to_excel(f'{self.local_target}\\{output_name}.xlsx', index=False, header=True)
        T1.insert(END, 'Data Transformation complete...')
        T1.config(state='disabled')

    def sql_edit(self, sql_file):
        date = date_text.get()
        date_limit = 'SET @date_limit :='
        year_month = 'SET @target_year_month :='
        sign = ';'
        set_date = f'{date_limit} \'{date}\'{sign}'
        year_month_extract = ''.join(date.split('-')[0:2])
        set_year_month = f'{year_month} \'{year_month_extract}\'{sign}'
        try:
            if self.server_connect:
                sftp = self.client.open_sftp()
                t_insert('Updating SQL file data...')
                with sftp.file(f'/var/lib/mysql-files/{sql_file}', 'r+') as file:
                    content = file.readlines()
                    with sftp.file(r'/var/lib/mysql-files/online_count.csv', 'w+') as file2:
                        for line in content:
                            if date_limit in line:
                                new_line = set_date
                                file2.write(f'{new_line}\n')
                            elif year_month in line:
                                new_line = set_year_month
                                file2.write(f'{new_line}\n')
                            else:
                                file2.write(line)
        except paramiko.SSHException as e:
            t_insert(e)
            self.client.close()
            raise
        except Exception as e:
            t_insert(e)
            self.client.close()
            raise


def database_login_par():
    """returns server login credentials from config file"""

    parser = RawConfigParser()
    parser.read("db-creds.cfg")
    return (parser.get('client', "user").strip(),
            parser.get('client', "password").strip())


def sql_file_names():
    """returns SQL file names from config file"""

    parser = RawConfigParser()
    parser.read("db-creds.cfg")
    return (parser.get('sql_script', "all_invoiced").strip(),
            parser.get('sql_script', "never_invoiced").strip(),
            parser.get('sql_script', "target_month").strip(),
            parser.get('sql_script', "not_target_month").strip())


def server_commands():
    """returns commands to be executed on remote server"""

    parser = RawConfigParser()
    parser.read("db-creds.cfg")
    return (parser.get('commands', "all_inv_cmd").strip(),
            parser.get('commands', "never_inv_cmd").strip(),
            parser.get('commands', "tar_month_inv_cmd").strip(),
            parser.get('commands', "tar_month_not_inv_cmd").strip())


def t_insert(msg):
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, msg)
    T1.config(state='disabled')


all_invoiced_sql, never_invoiced_sql, target_month_sql, not_target_month_sql = sql_file_names()
username, password = database_login_par()
all_inv_cmd, never_inv_cmd, tar_month_inv_cmd, tar_month_not_inv_cmd = server_commands()
print(never_inv_cmd)

ssh = SshUtility()
email = EmailApi()


def connect_button():
    return ssh.server_connect()


def all_invoiced():
    file_name = 'all_invoiced.csv'
    try:
        ssh.sql_edit(all_invoiced_sql)
    except AttributeError as e:
        t_insert(f'Please Establish a Connection and try again...\n\n {e}')
        raise
    else:
        ssh.exec_cmd(all_inv_cmd)
        ssh.file_copy(file_name)
        ssh.data_clean(file_name)


def never_invoiced():
    file_name = 'never_invoiced.csv'
    try:
        ssh.exec_cmd(all_inv_cmd)
    except AttributeError as e:
        t_insert(f'Please Establish a Connection and try again...\n\n {e}')
        raise
    else:
        ssh.file_copy(file_name)
        ssh.data_clean(file_name)


def tar_month_invoiced():
    file_name = 'tar_month_invoiced.csv'
    try:
        ssh.sql_edit(target_month_sql)
    except AttributeError as e:
        t_insert(f'Please Establish a Connection and try again...\n\n {e}')
        raise
    else:
        ssh.exec_cmd(tar_month_inv_cmd)
        ssh.file_copy(file_name)
        ssh.data_clean(file_name)


def tar_month_not_invoiced():
    file_name = 'tar_month_not_invoiced.csv'
    try:
        ssh.sql_edit(not_target_month_sql)
    except AttributeError as e:
        t_insert(f'Please Establish a Connection and try again...\n\n {e}')
        raise
    else:
        ssh.exec_cmd(tar_month_not_inv_cmd)
        ssh.file_copy(file_name)
        ssh.data_clean(file_name)


def all_report():
    tar_month_invoiced()
    never_invoiced()
    all_invoiced()
    tar_month_not_invoiced()


def email_button():
    return email.send_message()


window = Tk()
window.title('Monthly Invoiced Device Report Generator Version 0.1')

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

T1 = Text(window, height=15, width=40)
T1.grid(row=2, column=0, rowspan=8, columnspan=1, pady=(0, 0), padx=(20, 5))
T1.config(state='disabled')

b1 = Button(window, text='Test Con', width=15, command=connect_button)
b1.grid(row=2, column=1, pady=(0, 10), padx=(50, 30))

b2 = Button(window, text='All Invoiced', width=15, command=all_invoiced)
b2.grid(row=3, column=1, pady=(0, 10), padx=(50, 30))

b3 = Button(window, text='Never Invoiced', width=15, command=never_invoiced)
b3.grid(row=4, column=1, pady=(0, 10), padx=(50, 30))

b4 = Button(window, text='Target Invoiced', width=15, command=tar_month_invoiced)
b4.grid(row=5, column=1, pady=(0, 10), padx=(50, 30))

b5 = Button(window, text='Target Not Inv.', width=15)
b5.grid(row=6, column=1, pady=(0, 10), padx=(50, 30))

b6 = Button(window, text='All Report', width=15, command=all_report)
b6.grid(row=7, column=1, pady=(0, 10), padx=(50, 30))

b7 = Button(window, text='Email Report', width=15, command=email_button)
b7.grid(row=8, column=1, pady=(0, 10), padx=(50, 30))

b8 = Button(window, text='close', width=15, command=window.destroy)
b8.grid(row=9, column=1, pady=(0, 10), padx=(50, 30))

window.mainloop()
