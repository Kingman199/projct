# projct

Server_Side folder includes all the database files.

Client_Side folder includes all the webside files.


-----------------
# HOW TO RUN?
Here is how:
  1. Download the files
  2. Open the 2 folders: server_side, client_side in two separate folders windows
  3. Press on the path (for example)-->  C:\Users\user\your_folder_location\server_side
  4. *MAKE SURE YOU DO IT WHERE THE Main.py IS LOCACTED*
  5. type: cmd ,then and press Enter
  6. After the black window pops up:
  7. type: py Main.py
  8. after that - press Enter
  9. You should see something that looks like this at the end:

     *CLIENTS table created successfully

     FRIENDS table created successfully

     FRIEND_REQUESTS table created successfully

     Role table created successfully

     WORKERS table created successfully

     WORKER_REQUESTS table created successfully

     Projects table created successfully

     SharedProject table created successfully

     LIST_TO_DO table created successfully

     Tasks table created successfully.

     Comments table created successfully.

     Sprints table created successfully.

     SprintTasks table created successfully.

     Server started on ('0.0.0.0', 8085)*
  11. After that, go to your client_side folder: C:\Users\user\your_folder_location\client_side
  12. go to: client_side/ConnectionWithDatabase.py and open it with NotePad++
  13. Get the IP of the computer that runs the server_side, copy it into the ADDR where the string is:  ADDR = ("IP", 8085)
  14. After that, go to your client_side folder: C:\Users\user\your_folder_location\client_side
  15. *MAKE SURE YOU DO IT WHERE THE Main.py IS LOCACTED*
  16. type: cmd ,then and press Enter
  17. After the black window pops up:
  18. type py Main.py
  19. after that - press Enter
  20. You should see 4 links: DOUBLE CLICK ON THE WITH THE  --- :5000
  * Running on http://127.0.0.1:5001
 * Running on http://computer_ip:5001
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://computer_ip:5000 

#ENJOY! :D
