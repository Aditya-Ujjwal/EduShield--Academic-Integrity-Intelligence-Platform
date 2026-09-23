# EduShield — SQL Loading Layer

This folder contains the MySQL schema and Python loading workflow for the
cleaned EduShield relational datasets.

## Files

`sql/01_create_schema.sql`
Creates the `edushield` database and all 14 tables.

`sql/02_add_constraints.sql`
Adds foreign-key relationships after the CSV data has been loaded.

`sql/03_post_load_audit.sql`
Runs row-count, target-distribution, orphan, duplicate, and chronology checks.

`python/load_data.py`
Reads the cleaned CSVs from `data/processed`, normalizes dates/booleans/numeric
fields, loads the tables in dependency order, and validates row counts and
basic relationships.

## Load order

The Python loader uses:

`academic_terms → departments → majors → instructors → students → courses → course_offerings → assignments → submissions → detector_tools → ai_detector_results → student_behavior_events → integrity_cases → student_integrity_history`

## Environment

Create a `.env` file in the EduShield project root:

```text
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=edushield
```

Run the workflow from the project root:

```bash
python python/load_data.py
```

Then execute the two SQL scripts in MySQL Workbench:

```text
sql/02_add_constraints.sql
sql/03_post_load_audit.sql
```

The cleaned CSVs remain the source-of-truth data for the Power BI model.
