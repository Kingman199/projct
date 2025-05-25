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

### How to Temporarily Disable the Firewall in Windows

1. Click the `Start` or `Windows` button.  
2. Type **Firewall** and select **Windows Defender Firewall**.  
3. On the left menu, click **Turn Windows Defender Firewall on or off**.  
4. Under both sections (Private and Public), select:  
   - `Turn off Windows Defender Firewall`  
5. Click **OK** to save and close.

> Tip: If you're using a personal computer, remember to turn the firewall back on when you're done.  
> Just follow the same steps and re-select `Turn on Windows Defender Firewall` for both Private and Public.

---

## How to Find the Server Computer's IP Address

To connect the client to the server, you’ll need the IP address of the computer running the server.

### Here’s how to do it:

On the server computer, open Command Prompt (`cmd`) and run:  
```ipconfig```

Look for a line that says something like:  

```IPv4 Address. . . . . . . . . . . : your_computer_ip```

### Verify the computers are connected

On **any other computer (with its firewall off)**, open `cmd` and run:  
```ping your_other_computer_ip```

You should see something like:

```
Pinging your_other_computer_ip with 32 bytes of data:
...
Ping statistics for your_other_computer_ip:
Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
```

**Note:** If it doesn’t work, try the ping from another computer!

Once you find the IP, keep that command window open and proceed to the next steps.

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

