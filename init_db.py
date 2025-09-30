import sqlite3, os
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def init_hr():
    p = DATA_DIR / "hr.db"
    conn = sqlite3.connect(p)
    c = conn.cursor()
    
    # Drop existing tables first
    c.execute("DROP TABLE IF EXISTS employee_projects")
    c.execute("DROP TABLE IF EXISTS projects")
    c.execute("DROP TABLE IF EXISTS employees")
    c.execute("DROP TABLE IF EXISTS departments")
    
    # Enhanced HR schema - Create tables in dependency order
    c.execute('''CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        budget REAL,
        location TEXT,
        head_id INTEGER
    )''')
    
    c.execute('''CREATE TABLE employees (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        department TEXT,
        salary REAL,
        hire_date DATE,
        manager_id INTEGER,
        position TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(manager_id) REFERENCES employees(emp_id)
    )''')
    
    c.execute('''CREATE TABLE projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        start_date DATE,
        end_date DATE,
        budget REAL,
        status TEXT DEFAULT 'active',
        manager_id INTEGER,
        FOREIGN KEY(manager_id) REFERENCES employees(emp_id)
    )''')
    
    c.execute('''CREATE TABLE employee_projects (
        emp_id INTEGER,
        project_id INTEGER,
        role TEXT,
        hours_allocated INTEGER,
        PRIMARY KEY (emp_id, project_id),
        FOREIGN KEY(emp_id) REFERENCES employees(emp_id),
        FOREIGN KEY(project_id) REFERENCES projects(project_id)
    )''')
    
    
    # Insert departments
    departments = [
        ("Sales", 500000, "Floor 1", None),
        ("IT", 800000, "Floor 2", None),
        ("HR", 300000, "Floor 1", None),
        ("Marketing", 400000, "Floor 3", None),
        ("Finance", 350000, "Floor 1", None)
    ]
    c.executemany("INSERT INTO departments (name,budget,location,head_id) VALUES (?,?,?,?)", departments)
    
    # Insert employees
    employees = [
        ("Alice Johnson", "alice.johnson@company.com", "Sales", 75000, "2022-01-15", None, "Sales Manager", "active"),
        ("Bob Smith", "bob.smith@company.com", "IT", 85000, "2021-03-20", None, "Senior Developer", "active"),
        ("Charlie Brown", "charlie.brown@company.com", "HR", 65000, "2022-06-10", None, "HR Specialist", "active"),
        ("Diana Prince", "diana.prince@company.com", "Marketing", 70000, "2022-02-28", None, "Marketing Manager", "active"),
        ("Edward Norton", "edward.norton@company.com", "Finance", 68000, "2021-11-05", None, "Financial Analyst", "active"),
        ("Fiona Green", "fiona.green@company.com", "IT", 78000, "2022-04-12", 2, "Developer", "active"),
        ("George Wilson", "george.wilson@company.com", "Sales", 60000, "2022-08-20", 1, "Sales Rep", "active")
    ]
    c.executemany("INSERT INTO employees (name,email,department,salary,hire_date,manager_id,position,status) VALUES (?,?,?,?,?,?,?,?)", employees)
    
    # Insert projects
    projects = [
        ("Website Redesign", "Complete overhaul of company website", "2023-01-01", "2023-06-30", 150000, "completed", 2),
        ("Sales Analytics", "Implement new sales tracking system", "2023-03-01", "2023-08-31", 80000, "active", 1),
        ("Employee Portal", "New internal employee portal", "2023-05-01", "2023-12-31", 120000, "active", 2),
        ("Marketing Campaign Q4", "Q4 marketing campaign launch", "2023-10-01", "2023-12-31", 60000, "active", 4)
    ]
    c.executemany("INSERT INTO projects (name,description,start_date,end_date,budget,status,manager_id) VALUES (?,?,?,?,?,?,?)", projects)
    
    # Insert employee-project assignments
    assignments = [
        (2, 1, "Lead Developer", 40),
        (6, 1, "Developer", 30),
        (1, 2, "Project Owner", 20),
        (7, 2, "Data Analyst", 35),
        (2, 3, "Tech Lead", 35),
        (6, 3, "Developer", 40),
        (4, 4, "Campaign Manager", 40),
        (7, 4, "Sales Support", 15)
    ]
    c.executemany("INSERT INTO employee_projects (emp_id,project_id,role,hours_allocated) VALUES (?,?,?,?)", assignments)
    
    conn.commit()
    conn.close()

def init_healthcare():
    p = DATA_DIR / "healthcare.db"
    conn = sqlite3.connect(p)
    c = conn.cursor()
    
    # Drop existing tables first
    c.execute("DROP TABLE IF EXISTS medical_records")
    c.execute("DROP TABLE IF EXISTS appointments")
    c.execute("DROP TABLE IF EXISTS patients")
    c.execute("DROP TABLE IF EXISTS doctors")
    
    # Enhanced healthcare schema
    c.execute('''CREATE TABLE patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date_of_birth DATE,
        gender TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        insurance_id TEXT,
        emergency_contact TEXT,
        created_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT,
        license_number TEXT UNIQUE,
        phone TEXT,
        email TEXT,
        experience_years INTEGER,
        department TEXT,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE appointments (
        app_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        duration_minutes INTEGER DEFAULT 30,
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        diagnosis TEXT,
        treatment TEXT,
        prescription TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
    )''')
    
    c.execute('''CREATE TABLE medical_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        visit_date DATE,
        symptoms TEXT,
        diagnosis TEXT,
        treatment TEXT,
        prescription TEXT,
        follow_up_date DATE,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
    )''')
    
    
    # Insert doctors
    doctors = [
        ("Dr. Sarah Johnson", "Cardiology", "CARD123456", "555-0101", "sarah.johnson@hospital.com", 15, "Cardiology"),
        ("Dr. Michael Chen", "Neurology", "NEURO789012", "555-0102", "michael.chen@hospital.com", 12, "Neurology"),
        ("Dr. Emily Davis", "Pediatrics", "PED345678", "555-0103", "emily.davis@hospital.com", 8, "Pediatrics"),
        ("Dr. Robert Wilson", "Orthopedics", "ORTH901234", "555-0104", "robert.wilson@hospital.com", 20, "Orthopedics"),
        ("Dr. Lisa Martinez", "Internal Medicine", "INT567890", "555-0105", "lisa.martinez@hospital.com", 10, "Internal Medicine")
    ]
    c.executemany("INSERT INTO doctors (name,specialty,license_number,phone,email,experience_years,department) VALUES (?,?,?,?,?,?,?)", doctors)
    
    # Insert patients
    patients = [
        ("John Doe", "1985-03-15", "Male", "555-1001", "john.doe@email.com", "123 Main St", "INS001", "Jane Doe - 555-1002"),
        ("Jane Smith", "1990-07-22", "Female", "555-2001", "jane.smith@email.com", "456 Oak Ave", "INS002", "Bob Smith - 555-2002"),
        ("Mark Lee", "1978-12-03", "Male", "555-3001", "mark.lee@email.com", "789 Pine St", "INS003", "Mary Lee - 555-3002"),
        ("Sarah Johnson", "1992-05-18", "Female", "555-4001", "sarah.johnson@email.com", "321 Elm St", "INS004", "Tom Johnson - 555-4002"),
        ("David Brown", "1988-09-25", "Male", "555-5001", "david.brown@email.com", "654 Maple Ave", "INS005", "Lisa Brown - 555-5002")
    ]
    c.executemany("INSERT INTO patients (name,date_of_birth,gender,phone,email,address,insurance_id,emergency_contact) VALUES (?,?,?,?,?,?,?,?)", patients)
    
    # Insert appointments
    appointments = [
        (1, 1, "2025-01-15 10:00:00", 45, "completed", "Regular checkup", "Hypertension", "Lifestyle changes + medication", "Lisinopril 10mg daily"),
        (2, 2, "2025-01-16 14:30:00", 60, "completed", "Neurological exam", "Migraine", "Preventive medication", "Topiramate 50mg daily"),
        (3, 3, "2025-01-17 09:15:00", 30, "scheduled", "Pediatric consultation", None, None, None),
        (4, 4, "2025-01-18 11:00:00", 45, "scheduled", "Follow-up visit", None, None, None),
        (5, 5, "2025-01-19 15:45:00", 30, "scheduled", "Annual physical", None, None, None)
    ]
    c.executemany("INSERT INTO appointments (patient_id,doctor_id,appointment_date,duration_minutes,status,notes,diagnosis,treatment,prescription) VALUES (?,?,?,?,?,?,?,?,?)", appointments)
    
    # Insert medical records
    records = [
        (1, 1, "2025-01-15", "Chest pain, shortness of breath", "Hypertension", "Lifestyle changes + medication", "Lisinopril 10mg daily", "2025-02-15"),
        (2, 2, "2025-01-16", "Severe headaches, light sensitivity", "Migraine", "Preventive medication", "Topiramate 50mg daily", "2025-02-16")
    ]
    c.executemany("INSERT INTO medical_records (patient_id,doctor_id,visit_date,symptoms,diagnosis,treatment,prescription,follow_up_date) VALUES (?,?,?,?,?,?,?,?)", records)
    
    conn.commit()
    conn.close()

def init_ecommerce():
    p = DATA_DIR / "ecommerce.db"
    conn = sqlite3.connect(p)
    c = conn.cursor()
    
    # Drop existing tables first
    c.execute("DROP TABLE IF EXISTS order_items")
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS customers")
    
    # Ecommerce schema
    c.execute('''CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        registration_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        price REAL,
        stock_quantity INTEGER,
        sku TEXT UNIQUE,
        created_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        order_date DATE DEFAULT CURRENT_DATE,
        total_amount REAL,
        status TEXT DEFAULT 'pending',
        shipping_address TEXT,
        payment_method TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )''')
    
    c.execute('''CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        total_price REAL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )''')
    
    
    # Insert customers
    customers = [
        ("Alice Johnson", "alice.johnson@email.com", "555-1001", "123 Main St", "New York", "NY", "10001"),
        ("Bob Smith", "bob.smith@email.com", "555-2001", "456 Oak Ave", "Los Angeles", "CA", "90210"),
        ("Carol Davis", "carol.davis@email.com", "555-3001", "789 Pine St", "Chicago", "IL", "60601"),
        ("David Wilson", "david.wilson@email.com", "555-4001", "321 Elm St", "Houston", "TX", "77001")
    ]
    c.executemany("INSERT INTO customers (name,email,phone,address,city,state,zip_code) VALUES (?,?,?,?,?,?,?)", customers)
    
    # Insert products
    products = [
        ("Laptop Pro", "High-performance laptop", "Electronics", 1299.99, 50, "LAPTOP001"),
        ("Wireless Mouse", "Ergonomic wireless mouse", "Electronics", 29.99, 200, "MOUSE001"),
        ("Office Chair", "Ergonomic office chair", "Furniture", 299.99, 25, "CHAIR001"),
        ("Coffee Maker", "Automatic coffee maker", "Appliances", 149.99, 75, "COFFEE001"),
        ("Desk Lamp", "LED desk lamp", "Furniture", 49.99, 100, "LAMP001")
    ]
    c.executemany("INSERT INTO products (name,description,category,price,stock_quantity,sku) VALUES (?,?,?,?,?,?)", products)
    
    # Insert orders
    orders = [
        (1, "2025-01-10", 1329.98, "completed", "123 Main St, New York, NY 10001", "Credit Card"),
        (2, "2025-01-11", 349.98, "shipped", "456 Oak Ave, Los Angeles, CA 90210", "PayPal"),
        (3, "2025-01-12", 79.98, "pending", "789 Pine St, Chicago, IL 60601", "Credit Card")
    ]
    c.executemany("INSERT INTO orders (customer_id,order_date,total_amount,status,shipping_address,payment_method) VALUES (?,?,?,?,?,?)", orders)
    
    # Insert order items
    items = [
        (1, 1, 1, 1299.99, 1299.99),
        (1, 2, 1, 29.99, 29.99),
        (2, 3, 1, 299.99, 299.99),
        (2, 5, 1, 49.99, 49.99),
        (3, 4, 1, 149.99, 149.99),
        (3, 2, 1, 29.99, 29.99)
    ]
    c.executemany("INSERT INTO order_items (order_id,product_id,quantity,unit_price,total_price) VALUES (?,?,?,?,?)", items)
    
    conn.commit()
    conn.close()

def init_finance():
    p = DATA_DIR / "finance.db"
    conn = sqlite3.connect(p)
    c = conn.cursor()
    
    # Drop existing tables first
    c.execute("DROP TABLE IF EXISTS customer_accounts")
    c.execute("DROP TABLE IF EXISTS transactions")
    c.execute("DROP TABLE IF EXISTS accounts")
    c.execute("DROP TABLE IF EXISTS customers")
    
    # Finance schema
    c.execute('''CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT UNIQUE NOT NULL,
        account_type TEXT,
        balance REAL DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        status TEXT DEFAULT 'active',
        created_date DATE DEFAULT CURRENT_DATE
    )''')
    
    c.execute('''CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        address TEXT,
        date_of_birth DATE,
        ssn TEXT UNIQUE,
        created_date DATE DEFAULT CURRENT_DATE
    )''')
    
    c.execute('''CREATE TABLE transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        transaction_type TEXT,
        amount REAL,
        description TEXT,
        transaction_date DATE DEFAULT CURRENT_DATE,
        status TEXT DEFAULT 'completed',
        reference_number TEXT,
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    )''')
    
    c.execute('''CREATE TABLE customer_accounts (
        customer_id INTEGER,
        account_id INTEGER,
        relationship_type TEXT DEFAULT 'primary',
        PRIMARY KEY (customer_id, account_id),
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    )''')
    
    
    # Insert customers
    customers = [
        ("John Smith", "john.smith@email.com", "555-1001", "123 Main St", "1985-03-15", "123-45-6789"),
        ("Jane Doe", "jane.doe@email.com", "555-2001", "456 Oak Ave", "1990-07-22", "987-65-4321"),
        ("Bob Johnson", "bob.johnson@email.com", "555-3001", "789 Pine St", "1978-12-03", "456-78-9012")
    ]
    c.executemany("INSERT INTO customers (name,email,phone,address,date_of_birth,ssn) VALUES (?,?,?,?,?,?)", customers)
    
    # Insert accounts
    accounts = [
        ("ACC001", "Checking", 2500.00, "USD"),
        ("ACC002", "Savings", 15000.00, "USD"),
        ("ACC003", "Checking", 3200.00, "USD"),
        ("ACC004", "Savings", 8500.00, "USD"),
        ("ACC005", "Checking", 1800.00, "USD")
    ]
    c.executemany("INSERT INTO accounts (account_number,account_type,balance,currency) VALUES (?,?,?,?)", accounts)
    
    # Insert customer-account relationships
    relationships = [
        (1, 1, "primary"),
        (1, 2, "primary"),
        (2, 3, "primary"),
        (2, 4, "primary"),
        (3, 5, "primary")
    ]
    c.executemany("INSERT INTO customer_accounts (customer_id,account_id,relationship_type) VALUES (?,?,?)", relationships)
    
    # Insert transactions
    transactions = [
        (1, "deposit", 500.00, "Salary deposit", "2025-01-10", "completed", "TXN001"),
        (1, "withdrawal", -200.00, "ATM withdrawal", "2025-01-11", "completed", "TXN002"),
        (2, "deposit", 1000.00, "Interest payment", "2025-01-12", "completed", "TXN003"),
        (3, "transfer", -300.00, "Transfer to savings", "2025-01-13", "completed", "TXN004"),
        (4, "deposit", 300.00, "Transfer from checking", "2025-01-13", "completed", "TXN005")
    ]
    c.executemany("INSERT INTO transactions (account_id,transaction_type,amount,description,transaction_date,status,reference_number) VALUES (?,?,?,?,?,?,?)", transactions)
    
    conn.commit()
    conn.close()

def init_education():
    p = DATA_DIR / "education.db"
    conn = sqlite3.connect(p)
    c = conn.cursor()
    
    # Drop existing tables first
    c.execute("DROP TABLE IF EXISTS enrollments")
    c.execute("DROP TABLE IF EXISTS courses")
    c.execute("DROP TABLE IF EXISTS students")
    c.execute("DROP TABLE IF EXISTS instructors")
    
    # Education schema
    c.execute('''CREATE TABLE students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        date_of_birth DATE,
        enrollment_date DATE DEFAULT CURRENT_DATE,
        major TEXT,
        gpa REAL,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        credits INTEGER,
        department TEXT,
        instructor TEXT,
        semester TEXT,
        year INTEGER,
        status TEXT DEFAULT 'active'
    )''')
    
    c.execute('''CREATE TABLE enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        enrollment_date DATE DEFAULT CURRENT_DATE,
        grade TEXT,
        status TEXT DEFAULT 'enrolled',
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )''')
    
    c.execute('''CREATE TABLE instructors (
        instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        department TEXT,
        title TEXT,
        hire_date DATE,
        status TEXT DEFAULT 'active'
    )''')
    
    
    # Insert instructors
    instructors = [
        ("Dr. Sarah Wilson", "sarah.wilson@university.edu", "555-1001", "Computer Science", "Professor", "2020-01-15"),
        ("Dr. Michael Brown", "michael.brown@university.edu", "555-1002", "Mathematics", "Associate Professor", "2018-08-20"),
        ("Dr. Emily Davis", "emily.davis@university.edu", "555-1003", "Physics", "Professor", "2015-03-10"),
        ("Dr. Robert Johnson", "robert.johnson@university.edu", "555-1004", "English", "Assistant Professor", "2021-01-15")
    ]
    c.executemany("INSERT INTO instructors (name,email,phone,department,title,hire_date) VALUES (?,?,?,?,?,?)", instructors)
    
    # Insert students
    students = [
        ("Alice Johnson", "alice.johnson@student.edu", "555-2001", "2003-05-15", "2022-08-25", "Computer Science", 3.7),
        ("Bob Smith", "bob.smith@student.edu", "555-2002", "2002-11-22", "2021-08-25", "Mathematics", 3.5),
        ("Carol Davis", "carol.davis@student.edu", "555-2003", "2004-02-10", "2022-08-25", "Physics", 3.9),
        ("David Wilson", "david.wilson@student.edu", "555-2004", "2003-08-30", "2022-08-25", "English", 3.2)
    ]
    c.executemany("INSERT INTO students (name,email,phone,date_of_birth,enrollment_date,major,gpa) VALUES (?,?,?,?,?,?,?)", students)
    
    # Insert courses
    courses = [
        ("CS101", "Introduction to Programming", "Basic programming concepts", 3, "Computer Science", "Dr. Sarah Wilson", "Fall", 2024),
        ("CS201", "Data Structures", "Advanced data structures", 3, "Computer Science", "Dr. Sarah Wilson", "Fall", 2024),
        ("MATH101", "Calculus I", "Differential calculus", 4, "Mathematics", "Dr. Michael Brown", "Fall", 2024),
        ("PHYS101", "General Physics", "Mechanics and thermodynamics", 4, "Physics", "Dr. Emily Davis", "Fall", 2024),
        ("ENG101", "Composition", "Academic writing", 3, "English", "Dr. Robert Johnson", "Fall", 2024)
    ]
    c.executemany("INSERT INTO courses (course_code,title,description,credits,department,instructor,semester,year) VALUES (?,?,?,?,?,?,?,?)", courses)
    
    # Insert enrollments
    enrollments = [
        (1, 1, "2024-08-25", "A", "enrolled"),
        (1, 2, "2024-08-25", "B+", "enrolled"),
        (2, 3, "2024-08-25", "A-", "enrolled"),
        (3, 4, "2024-08-25", "A", "enrolled"),
        (4, 5, "2024-08-25", "B", "enrolled"),
        (1, 3, "2024-08-25", "A", "enrolled"),
        (2, 1, "2024-08-25", "B+", "enrolled")
    ]
    c.executemany("INSERT INTO enrollments (student_id,course_id,enrollment_date,grade,status) VALUES (?,?,?,?,?)", enrollments)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_hr()
    init_healthcare()
    init_ecommerce()
    init_finance()
    init_education()
    print("Databases created in data/ (hr.db, healthcare.db, ecommerce.db, finance.db, education.db)")
