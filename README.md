# QuizLab — Online Quiz Platform

QuizLab is a Python desktop application for creating and taking subject-based quizzes. It uses a Tkinter graphical interface and an SQLite database, with separate workflows for administrators and students.

## Features

### Administrator

- Add and manage subjects with a name, description, creation date, and active status.
- View each subject’s active quizzes, total quizzes, and the number of students who completed quizzes for it.
- Create and manage questions in the question bank.
- Create quizzes, add questions, and manage quiz status, including publishing and closing quizzes.

### Student

- View and take published quizzes.
- Complete timed quiz attempts and receive scores and pass/fail results.
- Review recent attempts and performance statistics.
- See completed quiz performance grouped by subject.
- View monthly charts showing completed quiz counts and average marks.

## Requirements

- Python 3.11 or later
- Matplotlib
- Tkinter, usually included with standard Python installations

Install Matplotlib using the same Python interpreter you will use to run the application:

```bash
python -m pip install matplotlib
```

If the project includes `requirements.txt`, install its listed dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Run the Application

Keep `quizlab_gui.py` and `quizlab.db` together in the same folder, then run:

```bash
python quizlab_gui.py
```

On Windows, if you have multiple Python installations, use the full path to the interpreter for both installation and launch:

```powershell
& "C:\Path\To\Python\python.exe" -m pip install matplotlib
& "C:\Path\To\Python\python.exe" quizlab_gui.py
```

Replace `C:\Path\To\Python\python.exe` with the location of your Python executable.

## Database

The application uses `quizlab.db`, an SQLite database located beside the application files. It stores user accounts, subjects, quizzes, questions, answer options, quiz attempts, and submitted answers. Keep a backup of this file if you need to preserve the application’s data.

## Default Accounts

The database setup file includes these initial accounts:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@gmail.com` | `admin@123` |
| Student | `student@gmail.com` | `student@123` |

Use these only with a local project copy whose database was initialized with the supplied setup. Change or remove default credentials before using the application with real users.

## Project Files

- `quizlab_gui.py` — Tkinter application interface and workflows.
- `database.py` — SQLite database schema and initial setup.
- `quizlab.db` — application data.
- `requirements.txt` — Python package requirements.
