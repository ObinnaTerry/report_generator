from tkinter import *
# from backend import SshUtility
import paramiko
import select
import socket, os
from configparser import RawConfigParser
import pandas as pd


def database_login_par():
    """returns server login credentials from config file"""

    parser = RawConfigParser()
    parser.read("db-creds.cfg")
    return (parser.get('client', "user").strip(),
            parser.get('client', "password").strip())


username, password = database_login_par()


def t_insert(msg):
    T1.config(state='normal')
    T1.delete('1.0', END)
    T1.insert(END, msg)
    T1.config(state='disabled')


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
            if self.server_connect():
                timeout = 5
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
                if not exit_code and not self.stderr_chunks:  # exit code zero usually implies no errors occurred
                    return t_insert(f"SQL query completed!..\n{''.join(self.stdout_chunks)}")

                if not exit_code and self.stderr_chunks:
                    # exit code zero returned, but stderr is not empty, this could imply minor issues or warnings
                    return t_insert(f"SQL query completed..\nPossible issues:\n{''.join(self.stderr_chunks)}")

                if len(self.stderr_chunks) > 0 and exit_code:  # non-zero exit code implies error
                    raise (MySqlScriptError(self.stderr_chunks))  # raises the MySqlScriptError class

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
            if self.server_connect():
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
        data.columns = ['TPIN', 'Tax_Payername', 'Terminal_ID', 'Taxpayer_Address', 'Tax_Office', 'Latest_Time', 'Issued', 'Total_Sales', 'Total_Tax', 'Sector']
        data.TPIN = data.TPIN.astype(str)
        data.Terminal_ID = data.Terminal_ID.astype(str)
        data.to_excel(f'{self.local_target}\\{output_name}.xlsx', index=False, header=True)
        T1.insert(END, 'Data Transformation complete...')
        T1.config(state='disabled')


ssh = SshUtility()


def connect_button():
    return ssh.server_connect()


# def data_one():
#     DataButtons(b1_file)
#     T1.config(state='normal')
#     T1.delete('1.0', END)
#     T1.insert(END, 'Task completed!')
#     T1.config(state='disabled')
#
#
# def data_two():
#     DataButtons(b2_file)
#     T1.config(state='normal')
#     T1.delete('1.0', END)
#     T1.insert(END, 'Task completed!')
#     T1.config(state='disabled')
#
#
# def data_three():
#     DataButtons(b3_file)
#     T1.config(state='normal')
#     T1.delete('1.0', END)
#     T1.insert(END, 'Task completed!')
#     T1.config(state='disabled')
#
#
# def data_four():
#     DataButtons(b4_file)
#     T1.config(state='normal')
#     T1.delete('1.0', END)
#     T1.insert(END, 'Task completed!')
#     T1.config(state='disabled')
#
#
# def test_data():
#     try:
#         DataButtons(b_test)
#     except:
#         raise
#     else:
#         T1.config(state='normal')
#         T1.delete('1.0', END)
#         T1.insert(END, 'Task completed!')
#         T1.config(state='disabled')


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

b1 = Button(window, text='data 1', width=15, command=connect_button)
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
