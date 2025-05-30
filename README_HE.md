
# מדריך התקנת הפרויקט  
ברוכים הבאים לפרויקט (Sunday.com)! בואו נתחיל בצורה חלקה ופשוטה.

## מבנה הפרויקט
Server_Side ───┤ # כל קבצי השרת והמסד נתונים נמצאים כאן

Client_Side ───┘ # כל קבצי הצד לקוח / אתר נמצאים כאן


---

## אם אתם מריצים את זה בבית הספר

**חשוב מאוד:**  
קודם כל — **כבו את חומת האש (Firewall)**  
(הרשתות של בתי הספר לפעמים קצת בעייתיות...)

### איך לכבות את חומת האש ב-Windows (באופן זמני)

1. לחצו על כפתור `Start` או `Windows`.
2. הקלידו **Firewall** ובחרו ב־**Windows Defender Firewall**.
3. בתפריט בצד שמאל, לחצו על **Turn Windows Defender Firewall on or off**.
4. תחת שתי הקטגוריות (Private ו־Public), סמנו את האפשרות:
   - `Turn off Windows Defender Firewall`
5. לחצו **OK** לשמירה וסגירה.

>  טיפ: זכרו להחזיר את ההגדרות לאחר סיום השימוש אם אתם במחשב אישי.

---
---
## איך למצוא את כתובת ה-IP של מחשב השרת?

כדי לחבר בין הלקוח לשרת, תצטרכו לדעת מה כתובת ה-IP של המחשב שבו רץ השרת.

### כך תעשו את זה:
כדי לעשות זאת, הריצו במחשב של השרת ב-cmd: 
 ```ipconfig```
חפשו שורה בשם: 
```IPv4 Address. . . . . . . . . . . : your_computer_ip```

ודאו שהמחשבים מקושרים: הריצו את הפקודה הזאת בכל מחשב **אחר שחומת המגן שלו כבוייה** - 

```ping your_other_computer_ip```


אתם אמורים לראות משהו כזה:

Pinging *your_other_computer_ip* with 32 bytes of data:

....

Ping statistics for *your_other_computer_ip*:

    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
**הערה : אם לא עבד לכם, עשו את בדיקת החיבור במחשב אחר!**

בתום תהליך זה, שימרו על הכתובת ה-IP (השאירו את ה-cmd פתוח)
ביצעו את פעולות הבאות:

## איך להפעיל את הפרויקט?

### שלב אחר שלב

1. הורידו את קבצי הפרויקט.
2. צרו שני פרויקטים חדשים ב-PyCharm (או לא, אם בא לכם לחסוך בזיכרון).
3. פתחו את התיקיות `Server_Side` ו־`Client_Side` כל אחת בחלון סייר קבצים נפרד.
4. בחרו את כל הקבצים כל הקבצים מתוך `Server_Side` וגררו אותם לתוך תיקיית הפרויקט הראשונה שלכם.
5. עשו את אותו הדבר עם `Client_Side` לתוך תיקיית הפרויקט השנייה.
6. גשו לתיקיית השרת, לדוגמה:

C:\Users\your_name\your_server_folder\...

7. ודאו שאתם בתיקייה שבה נמצא הקובץ `Main.py`.
8. לחצו על שורת הנתיב, הקלידו `cmd` ולחצו Enter.
9. בחלון השחור שנפתח, הקלידו:
py Main.py
10. אתם אמורים לראות בסוף:
 ```
 Server started on ('0.0.0.0', 8085)
 ```

---

### חיבור הלקוח לשרת

11. פתחו את הקובץ:
 ```
 client_side/ConnectionWithDatabase.py
 ```
 בעזרת Notepad++ או עורך טקסט אחר.
12. החליפו את `"IP"` בשורה הבאה:
 ```python
 ADDR = ("IP", 8085)
 ```
 לכתובת ה-IP של המחשב שמצאנו, זה שרץ השרת.

12.5 שמרו את קובץ/לחצו ctrl + s
 
---

### הרצת הצד לקוח

13. גשו לתיקיית הלקוח:
 ```
 C:\Users\your_name\your_client_folder\
 ```
14. ודאו שאתם בתיקייה שבה נמצא `Main.py`.
15. לחצו על שורת הנתיב, הקלידו `cmd` ולחצו Enter.
16. הקלידו:
 ```
 py Main.py
 ```
17. אם הכול עבד כמו שצריך, תראו משהו כזה:
 ```
 * Running on http://127.0.0.1:5000
 * Running on http://computer_ip:5000
 ```

**הערה:**  
זהו שרת פיתוח. 

---

## זהו, אתם מחוברים

כעת תוכלו לשתף את הקישור (`http://computer_ip:5000`) עם חברים כדי שיוכלו להצטרף.

---

# תיהנו מהפרויקט  
נבנה עם זמן, השקעה, והרבה מאוד אהבה. בהצלחה!
