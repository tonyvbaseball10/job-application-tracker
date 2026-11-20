"""Flask application for tracking companies, jobs, applications, and contacts."""

import json
import os
import re
from datetime import date

from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error, IntegrityError

from database import execute, fetch_all, fetch_one

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "development-only-change-me")

JOB_TYPES = ("Full-time", "Part-time", "Contract", "Internship")
APPLICATION_STATUSES = ("Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn")


def clean(value):
    return value.strip() if isinstance(value, str) else value


def optional_int(value, field_name):
    value = clean(value)
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a whole number.") from exc
    if number < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return number


def json_array(value, field_name="Requirements"):
    """Accept a JSON array or comma-separated text and return JSON text."""
    value = clean(value)
    if not value:
        return json.dumps([])
    try:
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError
        items = parsed
    except (json.JSONDecodeError, ValueError):
        items = [item.strip() for item in value.split(",") if item.strip()]
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise ValueError(f"{field_name} must contain skill names.")
    return json.dumps(list(dict.fromkeys(item.strip() for item in items)))


def json_object(value, field_name="JSON data"):
    value = clean(value)
    if not value:
        return json.dumps({})
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object.")
    return json.dumps(parsed)


def parse_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def normalize_skills(value):
    return {s.strip().casefold(): s.strip() for s in re.split(r"[,\n]", value or "") if s.strip()}


def calculate_matches(jobs, skills_text):
    """Rank jobs by percentage of required skills supplied by the user."""
    user_skills = normalize_skills(skills_text)
    results = []
    for job in jobs:
        requirements = parse_json(job.get("requirements"), [])
        required = {str(skill).strip().casefold(): str(skill).strip() for skill in requirements if str(skill).strip()}
        matched_keys = sorted(set(required) & set(user_skills))
        missing_keys = sorted(set(required) - set(user_skills))
        total = len(required)
        percentage = round(len(matched_keys) / total * 100) if total else 0
        results.append({
            **job,
            "requirements_list": list(required.values()),
            "matched": [required[key] for key in matched_keys],
            "missing": [required[key] for key in missing_keys],
            "matched_count": len(matched_keys),
            "required_count": total,
            "percentage": percentage,
        })
    return sorted(results, key=lambda row: (-row["percentage"], row["job_title"].casefold()))


@app.template_filter("money")
def money(value):
    return "—" if value in (None, "") else f"${int(value):,}"


@app.template_filter("prettyjson")
def prettyjson(value):
    return json.dumps(parse_json(value, {}), indent=2)


@app.context_processor
def inject_globals():
    return {"today": date.today().isoformat(), "JOB_TYPES": JOB_TYPES, "APPLICATION_STATUSES": APPLICATION_STATUSES}


@app.errorhandler(Error)
def handle_database_error(error):
    app.logger.exception("Database error")
    return render_template("error.html", message="The database request could not be completed. Check the MySQL setup and try again."), 500


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="The requested record or page was not found."), 404


@app.route("/")
def dashboard():
    stats = fetch_one("""
        SELECT
          (SELECT COUNT(*) FROM companies) AS companies,
          (SELECT COUNT(*) FROM jobs) AS jobs,
          (SELECT COUNT(*) FROM applications) AS applications,
          (SELECT COUNT(*) FROM contacts) AS contacts,
          (SELECT COUNT(*) FROM applications WHERE status = 'Interview') AS interviews,
          (SELECT COUNT(*) FROM applications WHERE status = 'Offer') AS offers
    """)
    statuses = fetch_all("SELECT status, COUNT(*) AS total FROM applications GROUP BY status ORDER BY total DESC")
    recent = fetch_all("""
        SELECT a.*, j.job_title, c.company_name
        FROM applications a JOIN jobs j ON a.job_id=j.job_id
        JOIN companies c ON j.company_id=c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC LIMIT 6
    """)
    return render_template("dashboard.html", stats=stats, statuses=statuses, recent=recent)


@app.route("/companies")
def companies():
    rows = fetch_all("""
        SELECT c.*, COUNT(DISTINCT j.job_id) AS job_count, COUNT(DISTINCT ct.contact_id) AS contact_count
        FROM companies c LEFT JOIN jobs j ON c.company_id=j.company_id
        LEFT JOIN contacts ct ON c.company_id=ct.company_id
        GROUP BY c.company_id ORDER BY c.company_name
    """)
    return render_template("companies.html", companies=rows)


@app.route("/companies/new", methods=["GET", "POST"])
@app.route("/companies/<int:record_id>/edit", methods=["GET", "POST"])
def company_form(record_id=None):
    company = fetch_one("SELECT * FROM companies WHERE company_id=%s", (record_id,)) if record_id else None
    if record_id and not company:
        return not_found(None)
    if request.method == "POST":
        name = clean(request.form.get("company_name"))
        if not name:
            flash("Company name is required.", "error")
        else:
            values = (name, clean(request.form.get("industry")), clean(request.form.get("website")),
                      clean(request.form.get("city")), clean(request.form.get("state")), clean(request.form.get("notes")))
            if record_id:
                execute("UPDATE companies SET company_name=%s, industry=%s, website=%s, city=%s, state=%s, notes=%s WHERE company_id=%s", values + (record_id,))
                flash("Company updated.", "success")
            else:
                execute("INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES (%s,%s,%s,%s,%s,%s)", values)
                flash("Company added.", "success")
            return redirect(url_for("companies"))
    return render_template("company_form.html", company=company)


@app.route("/companies/<int:record_id>/delete", methods=["POST"])
def company_delete(record_id):
    try:
        execute("DELETE FROM companies WHERE company_id=%s", (record_id,))
        flash("Company deleted.", "success")
    except IntegrityError:
        flash("Delete the company's jobs and contacts first.", "error")
    return redirect(url_for("companies"))


@app.route("/jobs")
def jobs():
    rows = fetch_all("""
        SELECT j.*, c.company_name, a.application_id, a.status
        FROM jobs j JOIN companies c ON j.company_id=c.company_id
        LEFT JOIN applications a ON j.job_id=a.job_id
        ORDER BY COALESCE(j.date_posted, '1000-01-01') DESC, j.job_id DESC
    """)
    for row in rows:
        row["requirements_list"] = parse_json(row.get("requirements"), [])
    return render_template("jobs.html", jobs=rows)


@app.route("/jobs/new", methods=["GET", "POST"])
@app.route("/jobs/<int:record_id>/edit", methods=["GET", "POST"])
def job_form(record_id=None):
    job = fetch_one("SELECT * FROM jobs WHERE job_id=%s", (record_id,)) if record_id else None
    if record_id and not job:
        return not_found(None)
    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
    if request.method == "POST":
        try:
            company_id = int(request.form.get("company_id", ""))
            title = clean(request.form.get("job_title"))
            job_type = request.form.get("job_type")
            salary_min = optional_int(request.form.get("salary_min"), "Minimum salary")
            salary_max = optional_int(request.form.get("salary_max"), "Maximum salary")
            if not title:
                raise ValueError("Job title is required.")
            if job_type not in JOB_TYPES:
                raise ValueError("Choose a valid job type.")
            if salary_min is not None and salary_max is not None and salary_max < salary_min:
                raise ValueError("Maximum salary must be at least the minimum salary.")
            requirements = json_array(request.form.get("requirements"))
            values = (company_id, title, job_type, salary_min, salary_max, clean(request.form.get("job_url")),
                      request.form.get("date_posted") or None, requirements)
            if record_id:
                execute("UPDATE jobs SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s, salary_max=%s, job_url=%s, date_posted=%s, requirements=%s WHERE job_id=%s", values + (record_id,))
                flash("Job updated.", "success")
            else:
                execute("INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", values)
                flash("Job added.", "success")
            return redirect(url_for("jobs"))
        except (ValueError, TypeError) as error:
            flash(str(error) or "Complete all required fields.", "error")
    return render_template("job_form.html", job=job, companies=companies_list)


@app.route("/jobs/<int:record_id>/delete", methods=["POST"])
def job_delete(record_id):
    try:
        execute("DELETE FROM jobs WHERE job_id=%s", (record_id,))
        flash("Job deleted.", "success")
    except IntegrityError:
        flash("Delete the application for this job first.", "error")
    return redirect(url_for("jobs"))


@app.route("/applications")
def applications():
    rows = fetch_all("""
        SELECT a.*, j.job_title, c.company_name
        FROM applications a JOIN jobs j ON a.job_id=j.job_id
        JOIN companies c ON j.company_id=c.company_id
        ORDER BY a.application_date DESC, a.application_id DESC
    """)
    return render_template("applications.html", applications=rows)


@app.route("/applications/new", methods=["GET", "POST"])
@app.route("/applications/<int:record_id>/edit", methods=["GET", "POST"])
def application_form(record_id=None):
    application = fetch_one("SELECT * FROM applications WHERE application_id=%s", (record_id,)) if record_id else None
    if record_id and not application:
        return not_found(None)
    jobs_list = fetch_all("""
        SELECT j.job_id, j.job_title, c.company_name FROM jobs j
        JOIN companies c ON j.company_id=c.company_id ORDER BY c.company_name, j.job_title
    """)
    if request.method == "POST":
        try:
            job_id = int(request.form.get("job_id", ""))
            application_date = request.form.get("application_date")
            status = request.form.get("status")
            if not application_date:
                raise ValueError("Application date is required.")
            if status not in APPLICATION_STATUSES:
                raise ValueError("Choose a valid status.")
            interview_data = json_object(request.form.get("interview_data"), "Interview data")
            values = (job_id, application_date, status, clean(request.form.get("resume_version")),
                      bool(request.form.get("cover_letter_sent")), interview_data)
            if record_id:
                execute("UPDATE applications SET job_id=%s, application_date=%s, status=%s, resume_version=%s, cover_letter_sent=%s, interview_data=%s WHERE application_id=%s", values + (record_id,))
                flash("Application updated.", "success")
            else:
                execute("INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES (%s,%s,%s,%s,%s,%s)", values)
                flash("Application added.", "success")
            return redirect(url_for("applications"))
        except (ValueError, TypeError, IntegrityError) as error:
            message = "That job already has an application." if isinstance(error, IntegrityError) else str(error)
            flash(message or "Complete all required fields.", "error")
    return render_template("application_form.html", application=application, jobs=jobs_list)


@app.route("/applications/<int:record_id>/delete", methods=["POST"])
def application_delete(record_id):
    execute("DELETE FROM applications WHERE application_id=%s", (record_id,))
    flash("Application deleted.", "success")
    return redirect(url_for("applications"))


@app.route("/contacts")
def contacts():
    rows = fetch_all("""
        SELECT ct.*, c.company_name FROM contacts ct
        JOIN companies c ON ct.company_id=c.company_id
        ORDER BY ct.contact_name
    """)
    return render_template("contacts.html", contacts=rows)


@app.route("/contacts/new", methods=["GET", "POST"])
@app.route("/contacts/<int:record_id>/edit", methods=["GET", "POST"])
def contact_form(record_id=None):
    contact = fetch_one("SELECT * FROM contacts WHERE contact_id=%s", (record_id,)) if record_id else None
    if record_id and not contact:
        return not_found(None)
    companies_list = fetch_all("SELECT company_id, company_name FROM companies ORDER BY company_name")
    if request.method == "POST":
        try:
            company_id = int(request.form.get("company_id", ""))
            name = clean(request.form.get("contact_name"))
            email = clean(request.form.get("email"))
            if not name:
                raise ValueError("Contact name is required.")
            if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                raise ValueError("Enter a valid email address.")
            values = (company_id, name, clean(request.form.get("title")), email, clean(request.form.get("phone")),
                      clean(request.form.get("linkedin_url")), clean(request.form.get("notes")))
            if record_id:
                execute("UPDATE contacts SET company_id=%s, contact_name=%s, title=%s, email=%s, phone=%s, linkedin_url=%s, notes=%s WHERE contact_id=%s", values + (record_id,))
                flash("Contact updated.", "success")
            else:
                execute("INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)", values)
                flash("Contact added.", "success")
            return redirect(url_for("contacts"))
        except (ValueError, TypeError) as error:
            flash(str(error) or "Complete all required fields.", "error")
    return render_template("contact_form.html", contact=contact, companies=companies_list)


@app.route("/contacts/<int:record_id>/delete", methods=["POST"])
def contact_delete(record_id):
    execute("DELETE FROM contacts WHERE contact_id=%s", (record_id,))
    flash("Contact deleted.", "success")
    return redirect(url_for("contacts"))


@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    skills = request.form.get("skills", "") if request.method == "POST" else ""
    results = []
    if request.method == "POST":
        if not normalize_skills(skills):
            flash("Enter at least one skill.", "error")
        else:
            jobs_list = fetch_all("""
                SELECT j.job_id, j.job_title, j.job_type, j.requirements, c.company_name
                FROM jobs j JOIN companies c ON j.company_id=c.company_id
            """)
            results = calculate_matches(jobs_list, skills)
    return render_template("job_match.html", skills=skills, results=results)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")

