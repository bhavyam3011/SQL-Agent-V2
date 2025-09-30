# llm_parser.py
"""
Gemini-based NL -> SQL parser (structured output).
Requires: `pip install google-genai` (or use the OpenAI-compat layer if you prefer).
This module:
 - Sends a schema-aware prompt + NL to Gemini
 - Requests a JSON response describing operation/sql
 - Performs server-side validation (whitelist operations, disallow DDL/dangerous keywords)
 - Returns a dict identical in shape to your previous parser:
   {
     "operation": "READ"|"CREATE"|"UPDATE"|"DELETE"|"UNKNOWN",
     "table": "employees",
     "sql": "SELECT ...",
     "metadata": {...},
     "target_db": "hr"
   }
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Global conversation memory
CONVERSATION_HISTORY = []
MAX_HISTORY_LENGTH = 10

# Use the Google GenAI client (recommended quickstart). See: https://ai.google.dev/gemini-api/docs/quickstart
try:
    import google.generativeai as genai
except Exception as e:
    genai = None
    # If you prefer the OpenAI compatibility layer, you can swap to openai client calls instead.

# ---- Configuration ----
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")  # choose a Gemini model you have access to
# Provide DB schema info here (keeps the prompt short and deterministic).
# Keep updated if schema changes.
SCHEMA = {
    "hr": {
        "employees": {
            "columns": ["emp_id", "name", "email", "department", "salary", "hire_date", "manager_id", "position", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT UNIQUE", "TEXT", "REAL", "DATE", "INTEGER", "TEXT", "TEXT DEFAULT 'active'"],
            "relationships": {
                "manager_id": "employees(emp_id)",
                "department": "departments(name)"
            }
        },
        "departments": {
            "columns": ["dept_id", "name", "budget", "location", "head_id"],
            "types": ["INTEGER PRIMARY KEY", "TEXT UNIQUE NOT NULL", "REAL", "TEXT", "INTEGER"],
            "relationships": {
                "head_id": "employees(emp_id)"
            }
        },
        "projects": {
            "columns": ["project_id", "name", "description", "start_date", "end_date", "budget", "status", "manager_id"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT", "DATE", "DATE", "REAL", "TEXT DEFAULT 'active'", "INTEGER"],
            "relationships": {
                "manager_id": "employees(emp_id)"
            }
        },
        "employee_projects": {
            "columns": ["emp_id", "project_id", "role", "hours_allocated"],
            "types": ["INTEGER", "INTEGER", "TEXT", "INTEGER"],
            "relationships": {
                "emp_id": "employees(emp_id)",
                "project_id": "projects(project_id)"
            }
        }
    },
    "healthcare": {
        "patients": {
            "columns": ["patient_id", "name", "date_of_birth", "gender", "phone", "email", "address", "insurance_id", "emergency_contact", "created_date", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "DATE", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "DATE DEFAULT CURRENT_DATE", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "doctors": {
            "columns": ["doctor_id", "name", "specialty", "license_number", "phone", "email", "experience_years", "department", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT", "TEXT UNIQUE", "TEXT", "TEXT", "INTEGER", "TEXT", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "appointments": {
            "columns": ["app_id", "patient_id", "doctor_id", "appointment_date", "duration_minutes", "status", "notes", "diagnosis", "treatment", "prescription"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "INTEGER", "DATETIME", "INTEGER DEFAULT 30", "TEXT DEFAULT 'scheduled'", "TEXT", "TEXT", "TEXT", "TEXT"],
            "relationships": {
                "patient_id": "patients(patient_id)",
                "doctor_id": "doctors(doctor_id)"
            }
        },
        "medical_records": {
            "columns": ["record_id", "patient_id", "doctor_id", "visit_date", "symptoms", "diagnosis", "treatment", "prescription", "follow_up_date"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "INTEGER", "DATE", "TEXT", "TEXT", "TEXT", "TEXT", "DATE"],
            "relationships": {
                "patient_id": "patients(patient_id)",
                "doctor_id": "doctors(doctor_id)"
            }
        }
    },
    "ecommerce": {
        "customers": {
            "columns": ["customer_id", "name", "email", "phone", "address", "city", "state", "zip_code", "registration_date", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT UNIQUE", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "DATE DEFAULT CURRENT_DATE", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "products": {
            "columns": ["product_id", "name", "description", "category", "price", "stock_quantity", "sku", "created_date", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT", "TEXT", "REAL", "INTEGER", "TEXT UNIQUE", "DATE DEFAULT CURRENT_DATE", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "orders": {
            "columns": ["order_id", "customer_id", "order_date", "total_amount", "status", "shipping_address", "payment_method"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "DATE DEFAULT CURRENT_DATE", "REAL", "TEXT DEFAULT 'pending'", "TEXT", "TEXT"],
            "relationships": {
                "customer_id": "customers(customer_id)"
            }
        },
        "order_items": {
            "columns": ["item_id", "order_id", "product_id", "quantity", "unit_price", "total_price"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "INTEGER", "INTEGER", "REAL", "REAL"],
            "relationships": {
                "order_id": "orders(order_id)",
                "product_id": "products(product_id)"
            }
        }
    },
    "finance": {
        "customers": {
            "columns": ["customer_id", "name", "email", "phone", "address", "date_of_birth", "ssn", "created_date"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT UNIQUE", "TEXT", "TEXT", "DATE", "TEXT UNIQUE", "DATE DEFAULT CURRENT_DATE"],
            "relationships": {}
        },
        "accounts": {
            "columns": ["account_id", "account_number", "account_type", "balance", "currency", "status", "created_date"],
            "types": ["INTEGER PRIMARY KEY", "TEXT UNIQUE NOT NULL", "TEXT", "REAL DEFAULT 0", "TEXT DEFAULT 'USD'", "TEXT DEFAULT 'active'", "DATE DEFAULT CURRENT_DATE"],
            "relationships": {}
        },
        "transactions": {
            "columns": ["transaction_id", "account_id", "transaction_type", "amount", "description", "transaction_date", "status", "reference_number"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "TEXT", "REAL", "TEXT", "DATE DEFAULT CURRENT_DATE", "TEXT DEFAULT 'completed'", "TEXT"],
            "relationships": {
                "account_id": "accounts(account_id)"
            }
        },
        "customer_accounts": {
            "columns": ["customer_id", "account_id", "relationship_type"],
            "types": ["INTEGER", "INTEGER", "TEXT DEFAULT 'primary'"],
            "relationships": {
                "customer_id": "customers(customer_id)",
                "account_id": "accounts(account_id)"
            }
        }
    },
    "education": {
        "students": {
            "columns": ["student_id", "name", "email", "phone", "date_of_birth", "enrollment_date", "major", "gpa", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT UNIQUE", "TEXT", "DATE", "DATE DEFAULT CURRENT_DATE", "TEXT", "REAL", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "instructors": {
            "columns": ["instructor_id", "name", "email", "phone", "department", "title", "hire_date", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT NOT NULL", "TEXT UNIQUE", "TEXT", "TEXT", "TEXT", "DATE", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "courses": {
            "columns": ["course_id", "course_code", "title", "description", "credits", "department", "instructor", "semester", "year", "status"],
            "types": ["INTEGER PRIMARY KEY", "TEXT UNIQUE NOT NULL", "TEXT NOT NULL", "TEXT", "INTEGER", "TEXT", "TEXT", "TEXT", "INTEGER", "TEXT DEFAULT 'active'"],
            "relationships": {}
        },
        "enrollments": {
            "columns": ["enrollment_id", "student_id", "course_id", "enrollment_date", "grade", "status"],
            "types": ["INTEGER PRIMARY KEY", "INTEGER", "INTEGER", "DATE DEFAULT CURRENT_DATE", "TEXT", "TEXT DEFAULT 'enrolled'"],
            "relationships": {
                "student_id": "students(student_id)",
                "course_id": "courses(course_id)"
            }
        }
    }
}

DANGEROUS_KEYWORDS = [
    "drop", "truncate", "alter", "create", "shutdown", "delete database", "attach", "detach",
    "replace", "grant", "revoke", "exec(", "execute(", "pragma", "attach database"
]

ALLOWED_OPS = {"SELECT": "READ", "INSERT": "CREATE", "UPDATE": "UPDATE", "DELETE": "DELETE"}

# ---- Utility ----
def _contains_dangerous(sql: str) -> bool:
    s = sql.lower()
    for kw in DANGEROUS_KEYWORDS:
        if kw in s:
            return True
    return False

def _normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(";") + ";"  # ensure single trailing semicolon

def _add_to_conversation_history(query: str, result: Dict[str, Any], target_db: str):
    """Add query and result to conversation history"""
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY.append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "result": result,
        "target_db": target_db
    })
    
    # Keep only recent history
    if len(CONVERSATION_HISTORY) > MAX_HISTORY_LENGTH:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-MAX_HISTORY_LENGTH:]

def _get_conversation_context() -> str:
    """Get recent conversation context for the prompt"""
    if not CONVERSATION_HISTORY:
        return ""
    
    context = "\nRecent conversation history:\n"
    for entry in CONVERSATION_HISTORY[-3:]:  # Last 3 queries
        context += f"- User: {entry['query']}\n"
        context += f"  SQL: {entry['result'].get('sql', 'N/A')}\n"
        context += f"  Operation: {entry['result'].get('operation', 'N/A')}\n\n"
    
    return context

def _build_enhanced_schema_text(target_db: str) -> str:
    """Build enhanced schema text with relationships and data types"""
    schema = SCHEMA.get(target_db)
    if not schema:
        return ""
    
    schema_lines = []
    for table, info in schema.items():
        columns = info.get("columns", [])
        types = info.get("types", [])
        relationships = info.get("relationships", {})
        
        # Build column descriptions
        col_descriptions = []
        for i, col in enumerate(columns):
            col_type = types[i] if i < len(types) else "TEXT"
            col_descriptions.append(f"{col} ({col_type})")
        
        schema_lines.append(f"- {table}: {', '.join(col_descriptions)}")
        
        # Add relationships
        if relationships:
            for col, ref in relationships.items():
                schema_lines.append(f"  → {col} references {ref}")
    
    return "\n".join(schema_lines)

def _detect_reference_intent(query: str) -> bool:
    """Detect if query references previous conversation"""
    reference_indicators = [
        "same", "previous", "last", "above", "before", "earlier",
        "that", "those", "this", "these", "it", "them"
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in reference_indicators)

def _build_advanced_sql(parsed: Dict[str, Any], target_db: str) -> str:
    """Build advanced SQL from parsed components"""
    operation = parsed.get("operation", "").upper()
    if operation != "SELECT":
        return ""
    
    # Build SELECT clause
    fields = parsed.get("fields", ["*"])
    if isinstance(fields, list):
        cols = ", ".join(fields)
    else:
        cols = fields
    
    sql_parts = [f"SELECT {cols}"]
    
    # Build FROM clause
    table = parsed.get("table")
    if table:
        sql_parts.append(f"FROM {table}")
    else:
        # Complex query without primary table - use the SQL directly
        return ""
    
    # Add JOINs
    joins = parsed.get("joins", [])
    if joins:
        for join in joins:
            sql_parts.append(join)
    
    # Add WHERE clause
    where = parsed.get("where", "")
    if where:
        sql_parts.append(f"WHERE {where}")
    
    # Add GROUP BY
    group_by = parsed.get("group_by", "")
    if group_by:
        sql_parts.append(f"GROUP BY {group_by}")
    
    # Add HAVING
    having = parsed.get("having", "")
    if having:
        sql_parts.append(f"HAVING {having}")
    
    # Add ORDER BY
    order_by = parsed.get("order_by", "")
    if order_by:
        sql_parts.append(f"ORDER BY {order_by}")
    
    # Add LIMIT
    limit = parsed.get("limit")
    if limit:
        sql_parts.append(f"LIMIT {limit}")
    
    return _normalize_sql(" ".join(sql_parts))

def _suggest_alternative_queries(error_type: str, original_query: str) -> List[str]:
    """Suggest alternative queries based on error type"""
    suggestions = []
    
    if error_type == "dangerous_sql_detected":
        suggestions.extend([
            "Try rephrasing to avoid administrative operations",
            "Use SELECT, INSERT, UPDATE, or DELETE operations only"
        ])
    elif error_type == "could_not_parse_model_output":
        suggestions.extend([
            "Try simplifying your request",
            "Break complex queries into smaller parts",
            "Be more specific about table and column names"
        ])
    elif error_type == "failed_to_build_sql":
        suggestions.extend([
            "Ensure you're referencing valid table and column names",
            "Check the database schema for available tables",
            "Try a simpler query structure"
        ])
    
    return suggestions

# ---- Main function ----
def llm_parse_to_action(nl_text: str, target_db: str = "hr") -> Dict[str, Any]:
    """
    Return a structured action dict:
    {
      "operation": "READ"|"CREATE"|"UPDATE"|"DELETE"|"UNKNOWN",
      "table": "employees",
      "sql": "SELECT ...;",
      "metadata": {...},
      "target_db": target_db
    }
    """

    if genai is None:
        raise RuntimeError("google-generativeai client not available. pip install google-generativeai or set up an alternative client.")
    
    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable not set. Please set your Gemini API key.")

    # Build enhanced schema snippet for the model
    schema_text = _build_enhanced_schema_text(target_db)
    if not schema_text:
        raise ValueError(f"Unknown target_db: {target_db}")
    
    # Get conversation context
    conversation_context = _get_conversation_context()
    is_reference_query = _detect_reference_intent(nl_text)

    # Enhanced prompt with advanced SQL support
    system_prompt = (
        "You are an advanced SQL generation assistant. Given a user's natural language request and a database schema, "
        "produce a JSON object with the following keys:\n"
        "  - operation: one of [SELECT, INSERT, UPDATE, DELETE] (uppercase) or UNKNOWN\n"
        "  - table: primary table name from the schema (or null for complex queries)\n"
        "  - fields: list of fields to select or insert/update (use ['*'] for all)\n"
        "  - where: a SQL WHERE clause (without the 'WHERE' keyword) or empty string\n"
        "  - values: for INSERT provide a dict of column: value, or for UPDATE provide dict of column: value\n"
        "  - joins: list of JOIN clauses (e.g., ['JOIN table2 ON table1.id = table2.foreign_id'])\n"
        "  - group_by: GROUP BY clause fields (without 'GROUP BY' keyword)\n"
        "  - having: HAVING clause (without 'HAVING' keyword)\n"
        "  - order_by: ORDER BY clause (without 'ORDER BY' keyword)\n"
        "  - limit: LIMIT clause number (integer or null)\n"
        "  - sql: the final SQL statement (terminated by semicolon). Use only the tables/columns in the schema.\n"
        "\nAdvanced SQL Features Supported:\n"
        "  - JOINs: INNER, LEFT, RIGHT, FULL OUTER joins between tables\n"
        "  - Subqueries: Use parentheses for nested queries\n"
        "  - Aggregations: COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING\n"
        "  - Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)\n"
        "  - CTEs: WITH clause for Common Table Expressions\n"
        "  - Complex WHERE conditions with AND, OR, IN, EXISTS, NOT EXISTS\n"
        "\nImportant constraints:\n"
        "  - DO NOT generate any DDL (CREATE/DROP/ALTER) or dangerous admin statements.\n"
        "  - Keep SQL standard SQLite-compatible.\n"
        "  - Use proper JOIN syntax with ON conditions.\n"
        "  - For complex queries, break them into logical components in the JSON.\n"
        "\nReturn ONLY valid JSON (no extra commentary). Use null for empty fields when needed."
    )

    user_prompt = (
        f"Schema for target_db='{target_db}':\n{schema_text}\n\n"
        f"{conversation_context}"
        f"User request: '''{nl_text}'''\n\n"
        f"{'Note: This query appears to reference previous conversation context. Consider the recent queries above.' if is_reference_query else ''}\n\n"
        "Produce the JSON now."
    )

    
    # Configure the API key
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Combine system and user prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    # Use a content generation call — ask the model to output JSON only
    response = model.generate_content(
        full_prompt,
        # You can set temperature=0 for deterministic output
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,
            max_output_tokens=800
        )
    )

    # Extract text from response
    text = response.text

    # Try to find first JSON object in the text
    json_str = None
    m = re.search(r"(\{.*\})", text, re.S)
    if m:
        json_str = m.group(1)
    else:
        # fallback: entire text maybe JSON
        json_str = text.strip()

    try:
        parsed = json.loads(json_str)
    except Exception as e:
        # If parsing fails, return UNKNOWN
        return {"operation": "UNKNOWN", "sql": None, "metadata": {"error": "could_not_parse_model_output", "model_text": text}, "target_db": target_db}

    # Enhanced SQL generation with advanced features
    sql = parsed.get("sql") or ""
    if not sql and parsed.get("operation") == "SELECT":
        sql = _build_advanced_sql(parsed, target_db)
        if not sql:
            error_result = {
                "operation": "UNKNOWN", 
                "sql": None, 
                "metadata": {
                    "error": "failed_to_build_sql",
                    "suggestions": _suggest_alternative_queries("failed_to_build_sql", nl_text)
                }, 
                "target_db": target_db
            }
            _add_to_conversation_history(nl_text, error_result, target_db)
            return error_result

    sql = sql.strip()
    # block dangerous keywords
    if _contains_dangerous(sql):
        error_result = {
            "operation": "UNKNOWN", 
            "sql": None, 
            "metadata": {
                "error": "dangerous_sql_detected", 
                "sql_snippet": sql,
                "suggestions": _suggest_alternative_queries("dangerous_sql_detected", nl_text)
            }, 
            "target_db": target_db
        }
        _add_to_conversation_history(nl_text, error_result, target_db)
        return error_result

    # Determine operation canonical
    op_word = parsed.get("operation", "").upper()
    op = ALLOWED_OPS.get(op_word, None)
    if not op:
        # Try guessing from SQL
        if sql.strip().lower().startswith("select"):
            op = "READ"
        elif sql.strip().lower().startswith("insert"):
            op = "CREATE"
        elif sql.strip().lower().startswith("update"):
            op = "UPDATE"
        elif sql.strip().lower().startswith("delete"):
            op = "DELETE"
        else:
            op = "UNKNOWN"

    # Ensure semicolon and basic formatting
    sql = _normalize_sql(sql)

    table = parsed.get("table") or ""
    
    # Add business logic hints based on query patterns
    business_hints = _generate_business_hints(nl_text, op, table, target_db)
    
    result = {
        "operation": op,
        "table": table,
        "sql": sql,
        "metadata": {
            **parsed,
            "business_hints": business_hints,
            "conversation_context": is_reference_query
        },
        "target_db": target_db
    }
    
    # Add to conversation history
    _add_to_conversation_history(nl_text, result, target_db)
    
    return result

def _generate_business_hints(query: str, operation: str, table: str, target_db: str) -> List[str]:
    """Generate business logic hints based on query patterns"""
    hints = []
    query_lower = query.lower()
    
    # Performance hints
    if "count" in query_lower and operation == "READ":
        hints.append("Consider adding indexes on frequently queried columns for better performance")
    
    if "salary" in query_lower and ">" in query_lower:
        hints.append("Consider creating an index on salary column for range queries")
    
    # Business logic hints
    if target_db == "hr":
        if "salary" in query_lower and "average" in query_lower:
            hints.append("Consider calculating median salary for better representation of typical employee compensation")
        
        if "department" in query_lower and "count" in query_lower:
            hints.append("This could be useful for workforce planning and department sizing")
    
    elif target_db == "healthcare":
        if "appointment" in query_lower and "date" in query_lower:
            hints.append("Consider adding date range filters to avoid loading excessive historical data")
        
        if "patient" in query_lower and "diagnosis" in query_lower:
            hints.append("Ensure HIPAA compliance when handling patient diagnosis data")
    
    # Data quality hints
    if "null" in query_lower or "empty" in query_lower:
        hints.append("Consider adding data validation to prevent null values in critical fields")
    
    return hints
