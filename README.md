# Report Generator

Well, I got tired of connecting to our remote DB and decided to write python program that will automate a lot of the process. 

This is a desktop app made with python tkinter. The idea is to, with a click of a button, connect to a remote DB, run desired SQL script, and copy the output to your local host. Want to email the report out? Thats also just another button away!

**Dependencies**
- pandas
- import paramiko
- googleapiclient


**Possible Changes!**
With little modification, this program can be scheduled to run on a linux or windows OS and automatically generate reports with zero intervention (use google to find out how). But since I hope to share the program with my colleagues for general use, I will stick with the desktop GUI.