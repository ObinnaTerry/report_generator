import paramiko
import select
import socket
from configparser import RawConfigParser


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

    def connect(self):

        """'Establishes connection to the remote server"""

        t_insert('Setting Up SSH Connection...\n')
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname='', username=username, password=password)
            T1.config(state='normal')
            T1.insert(END, 'Successfully Connected!')
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
            if self.connect():
                timeout = 5
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
                    return t_insert(f"SQL query completed..\nPossible issues:\n{''.join(self.stdout_chunks)}")

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