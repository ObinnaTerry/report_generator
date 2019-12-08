import mysql.connector
from mysql.connector import Error


class Data:

    def __init__(self, ip):
        self.ip = ip

        try:
            self.server = mysql.connector.connect(host=self.ip,
                                                  database='sx_ims',
                                                  user='inspur',
                                                  password='Inspur@2018#ims')
            if self.server.is_connected():
                db_info = self.server.get_server_info()
                self.conn_status = "Connected to MySQL server1 database... MySQL Server version on ", db_info
            self.cursor = self.server.cursor()
            self.cursor.execute("select database();")
            record = self.cursor.fetchone()
            self.conn_to = "You are connected to - ", record

        except Error as e:
            self.err = "Error while connecting to MySQL", e

    def query(self, sql_query):
        self.cursor.execute(f"{sql_query}")

    def close_conn(self):
        self.cursor.close()
        self.server.close()

    @staticmethod
    def format_script(file, date):
        with open(file, 'r') as file:
            file = file.read().splitlines()
            file[0] = file[0].replace(';', f'{date};')
            sql = ''.join(file)
        return sql


#print(format_script('all_issued.sql', '2019-12-01'))