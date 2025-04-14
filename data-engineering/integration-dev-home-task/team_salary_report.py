import os
import requests
import logging
from dotenv import load_dotenv
import sqlite3
import pandas as pd

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def fetch_employee_data() -> dict:
    """
    Fetch employee data from the API using an API token from .env.
    Falls back to mock data if the API call fails.
    """
    api_token = os.getenv("API_TOKEN")
    url = "https://apim.workato.com/taboola-dev/homework-exam-v1/api/get_employees"
    headers = {"API-TOKEN": api_token}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            logging.info("Fetched employee data from API.")
            return response.json()
    except Exception as e:
        logging.warning(f"API call failed: {e}")

    logging.warning("Returning  employee data...")
    return {"employees": ""}



def insert_employees_to_db(employees: dict, db_name: str = ":memory:") -> sqlite3.Connection:
    """
    Inserts employee data into a local SQLite database.
    Returns the open DB connection so we can run queries later.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create the Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            EmployeeID INTEGER PRIMARY KEY,
            Name TEXT,
            Salary INTEGER,
            ManagerID INTEGER
        );
    """)
    logging.info("Created Employees table.")

    # Insert employee rows
    cursor.executemany("""
        INSERT INTO Employees (EmployeeID, Name, Salary, ManagerID)
        VALUES (:EmployeeID, :Name, :Salary, :ManagerID)
    """, employees)

    conn.commit()
    logging.info(f"Inserted {len(employees)} employees into the database.")
    return conn

def run_total_team_salary_query(conn: sqlite3.Connection, save_to: str = None) -> pd.DataFrame:
    """
    Runs the recursive SQL query to calculate TotalTeamSalary for each employee.
    Returns the result as a pandas DataFrame.
    Optionally saves the result to a local CSV.
    Note: You could also save to Google Sheets, S3, BigQuery, etc.
    """
    query = """
    WITH RECURSIVE TeamHierarchy AS (
        SELECT 
            EmployeeID,
            ManagerID,
            Salary,
            EmployeeID AS RootEmployee
        FROM Employees
        WHERE EmployeeID IS NOT NULL

        UNION ALL

        SELECT 
            e.EmployeeID,
            e.ManagerID,
            e.Salary,
            th.RootEmployee
        FROM Employees e
        JOIN TeamHierarchy th ON e.ManagerID = th.EmployeeID
        WHERE e.EmployeeID != e.ManagerID
    )
    SELECT 
        RootEmployee AS EmployeeID,
        SUM(Salary) AS TotalTeamSalary
    FROM TeamHierarchy
    GROUP BY RootEmployee
    ORDER BY EmployeeID;
    """

    df = pd.read_sql_query(query, conn)

    if save_to:
        df.to_csv(save_to, index=False)
        logging.info(f"Result saved to: {save_to}")

    return df


def main():
    data = fetch_employee_data()
    if "employees" not in data or not isinstance(data["employees"], list):
        logging.error("No valid employee data found. Exiting.")
        return

    conn = insert_employees_to_db(data["employees"])
    df = run_total_team_salary_query(conn, save_to="team_salary_results.csv")
    print("\nFinal Result:\n")
    print(df.head())


if __name__ == "__main__":
    main()