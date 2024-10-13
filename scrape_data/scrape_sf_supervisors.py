import requests
from bs4 import BeautifulSoup
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="sf_politics",
    user="nmarks"
)
cur = conn.cursor()
# Create the table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS supervisors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        district VARCHAR(50),
        website TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()  # Commit the transaction


# Scrape the San Francisco Supervisors' website
url = "https://sfbos.org/"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')


with open('soup_output.html', 'w', encoding='utf-8') as file:
    file.write(soup.prettify())

# Example: Find supervisor information (adjust the selectors to match the website's structure)
supervisors = soup.find_all('div', class_='slidetext')

# Function to check if supervisor exists in the database
def supervisor_exists(name):
    cur.execute("SELECT id FROM supervisors WHERE name = %s", (name,))
    return cur.fetchone() is not None

# Function to update supervisor's info if it already exists
def update_supervisor(name, district, contact_info, office_address, biography, website):
    cur.execute("""
        UPDATE supervisors
        SET district = %s, contact_info = %s, office_address = %s, biography = %s, website = %s, updated_at = NOW()
        WHERE name = %s
    """, (district, contact_info, office_address, biography, website, name))

# Function to insert a new supervisor
def insert_supervisor(name, district, contact_info, office_address, biography, website):
    cur.execute("""
        INSERT INTO supervisors (name, district, contact_info, office_address, biography, website)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, district, contact_info, office_address, biography, website))

# Loop through the found supervisor blocks
for supervisor in supervisors:
    # Extract the link element
    link = supervisor.find('a')
    # Get the full name and district from the text
    name_district = link.text.strip()
    
    # Separate the district and supervisor name (assuming it's in the format "District 08 - Supervisor <br> Rafael Mandelman")
    # Assuming the format is "District 08 - Supervisor Rafael Mandelman"
    parts = name_district.split(' - ')
    if len(parts) == 2:
        district = parts[0].strip()
        name = parts[1].replace('Supervisor', '').strip()
    else:
        # Handle unexpected format
        district = "Unknown"
        name = name_district.strip()
    
    # Extract the supervisor's webpage URL
    supervisor_url = link['href']

    print(f"Name: {name}, District: {district}, URL: {supervisor_url}")

    cur.execute("""
        INSERT INTO supervisors (name, district, website)
        VALUES (%s, %s, %s)
    """, (name, district, supervisor_url))

# Commit the transaction
conn.commit()

# Close the connection
cur.close()
conn.close()
