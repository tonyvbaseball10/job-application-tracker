# Job Application Tracker

A Flask and MySQL web application for organizing companies, job opportunities, applications, contacts, and job-to-skill matches.

## Features

- Dashboard statistics and recent application pipeline
- Full create, read, update, and delete workflows for all four required tables
- MySQL foreign keys, validation, indexes, enums, and JSON columns
- Job Match ranking with percentage, matched skills, and missing skills
- Responsive, consistent interface with delete confirmation and feedback messages
- Environment-based database configuration

## Requirements

- Python 3.10 or newer
- MySQL 8.0 or newer
- Git

## Fresh-clone setup

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/tonyvbaseball10/job-application-tracker.git
   cd job-application-tracker
   ```

2. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS or Linux**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create the MySQL database. This recreates `job_tracker` and loads sample data:

   **Windows PowerShell**

   ```powershell
   cmd /c "mysql -u root -p < schema.sql"
   ```

   If `mysql` is not on PATH, start it using its full installation path:

   ```powershell
   & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
   ```

   Then run `SOURCE C:/full/path/to/job-application-tracker/schema.sql;` at the `mysql>` prompt.

   **macOS or Linux**

   ```bash
   mysql -u root -p < schema.sql
   ```

   MySQL Workbench can also open and execute `schema.sql`.

5. Copy `.env.example` to `.env`, then enter your MySQL password and a random Flask secret:

   **Windows PowerShell**

   ```powershell
   Copy-Item .env.example .env
   ```

   **macOS or Linux**

   ```bash
   cp .env.example .env
   ```

6. Start the application:

   ```bash
   python -m flask --app app run --debug
   ```

7. Open `http://127.0.0.1:5000`.

## Configuration

The app reads these environment variables from `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DB_HOST` | `localhost` | MySQL server hostname |
| `DB_PORT` | `3306` | MySQL server port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | empty | MySQL password |
| `DB_NAME` | `job_tracker` | Database name |
| `FLASK_SECRET_KEY` | development value | Signs Flask session messages |

## Job Match behavior

The `jobs.requirements` column stores a JSON array such as `["Python", "SQL", "Flask"]`. Job Match:

1. Splits user skills on commas or new lines.
2. Normalizes capitalization and removes duplicates.
3. Compares the supplied skills with each job's requirements.
4. Calculates `matched skills / required skills × 100`.
5. Sorts jobs from highest to lowest percentage.

## Database relationships

- A company has many jobs.
- A company has many contacts.
- A job can have one tracked application.
- Parent records cannot be deleted while dependent records exist; the interface explains what must be removed first.

## Demo checklist

Record a 3–7 minute video showing:

1. MySQL with all four tables and sample rows.
2. The Flask server starting successfully.
3. Dashboard statistics.
4. Add, edit, and delete flows for each table.
5. A Job Match search showing percentages and missing skills.
6. The GitHub repository files.

## Submission notes

- Add the required recorded video file to the repository before submission.
- `AI_USAGE.md` documents the GenAI assistance used during development.
- Never commit `.env` or a real database password.

