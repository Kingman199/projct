# Project Setup Guide  
Welcome to the project (Sunday.com)! Let’s get you up and running smoothly.

## Project Structure
├── Server_Side # All the backend & database stuff lives here

└── Client_Side # All the frontend / website files are here

---

## If You're Running This at School

**IMPORTANT:**  
First things first — **TURN OFF YOUR FIREWALL!**  
(School networks can be... picky.)

---

## How to Run the Project

### Step-by-step Instructions
  1. Download the project files.
  2. Create two new folders (or don't — save that memory space if you want).
  3. Open both `Server_Side` and `Client_Side` folders in separate File Explorer windows.
  4. Drag everything from `Server_Side` into your first project folder.
  5. Do the same with `Client_Side` into your second project folder.
  6. Navigate to your server folder (example):
  7. Make sure you’re in the same folder as `Main.py`.
  8. In the path bar, type `cmd` and hit Enter.
  9. In the command window, run:
  10. You should see:
 ```
 Server started on ('0.0.0.0', 8085)
 ```

---

### Connect Client to Server

11. Open the file:
 ```
 client_side/ConnectionWithDatabase.py
 ```
 using Notepad++ or any code editor.
12. Replace `"IP"` in the following line:
 ```python
 ADDR = ("IP", 8085)
 ```
 with the IP address of the computer running the server.

---

### Run the Client Side

13. Navigate to your client folder:
 ```
 C:\Users\your_name\your_client_folder\
 ```
14. Make sure you're in the folder with `Main.py`.
15. In the path bar, type `cmd` and press Enter.
16. Run the client:
 ```
 py Main.py
 ```
17. If successful, you’ll see output like:
 ```
 * Running on http://127.0.0.1:5000
 * Running on http://computer_ip:5000
 ```

**Note:**  
This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.

---

## You're Live

You can now share your link (`http://computer_ip:5000`) with friends so they can join.

---

# Enjoy the Project  
Built with time, effort, and probably too much love. Have fun!

