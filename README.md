# Quîz Matrîx
#### Video Demo: <URL HERE>
#### Description:

Hello. MY name is Devansh Rajai.
I am a grade 9 coder pursuing this course to earn a baseline knowledge about coding.

This is my final project Quîz Matrîx.

Let me explain to you about this project.

Firstly, I was making a different project named as Da Recover for the final project, drawing inspirations from the Week 4 Problem Set Recover.
However, since it was getting too hard, I jumped onto this project.

I thought that a quiz website will suit such a final project the most since having users take quizzes, create them, and handling the scores requires a good grasp on SQL.
Also, making a dynamic website means a grasp on HTML and Python, which I'm trying to prove.

Now, let me discuss about the routes this website has:
    ⇛ /login route: Allows the users to log into the website.
    ⇛ /register route: Allows new users to register under a unique username.
    ⇛ /home route: A casual greeting to user, and also exhibits all quizzes to the user.
    ⇛ Essence of this website: The three routes that are the actually productive parts of this website:
         ⇶ /create & /add routes: The real essence of this website. They allow users to create quizzes.
         ⇶ /play/<int:quiz_id> route: This route lets users play quizzes.
    ⇛ /me route: This route lets users:
        ⇶ Change username
        ⇶ Change their profile pictures or logo
        ⇶ Allow them to edit the title or descriptions of their quizzes
        ⇶ See which users took their quizzes and how much they scored
        ⇶ Delete their account
    ⇛ /contact route: This route lets the users send the Developer[me] messages through the website.
                       For security reasons, I have used a Resend Account to get my mails from here.

Now, let me briefly detail about the files created in this folder.
    ⇛ app.py: Lifeline of this website, contains all of the route  logic and database connections.
    ⇛ requirements.txt: Lists all Python libraries and packages you need to run this website.
    ⇛ templates/: Contains all html files of the website which collectively form the face of the website, the place of interaction between the code and the user.
    ⇛ static/: Contains style.css, error.png and avatar.png, which form the design of the website.
    ⇛ quiz.db: The hard drive of this website. It contains user data, quiz data and user scores.

To run this website, follow the given steps:
    (1) Open up your terminal window, and run the following commands:
    ↪ 'pip install -r requirements.txt'
    (2) After running this command, run this command:
    ↪ 'flask run'

Credits:
    Email contact system: Resend
    HTML sytling system: Bootstrap
    AI Collaborator: Gemini
