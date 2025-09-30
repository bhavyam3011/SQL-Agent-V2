"""
LangGraph-based NL -> SQL parser with agent workflow
Requires: pip install langchain langgraph langchain-google-genai
"""

import os
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
import operator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI as genai   

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from dotenv import load_dotenv


load_dotenv()

# Import schema from existing parser
from llm_parser import SCHEMA, DANGEROUS_KEYWORDS, ALLOWED_OPS

# ==================== State Definition ====================
class AgentState(TypedDict):
    """State for the SQL generation agent"""
    messages: Annotated[List, operator.add]
    nl_query: str
    target_db: str
    operation: Optional[str]
    table: Optional[str]
    sql: Optional[str]
    metadata: Dict[str, Any]
    error: Optional[str]
    conversation_history: List[Dict]
    business_hints: List[str]
    risk_assessment: Dict[str, Any]


# ==================== Tools ====================
@tool
def validate_sql_safety(sql: str) -> Dict[str, Any]:
    """Validate SQL for dangerous operations"""
    sql_lower = sql.lower()
    
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_lower:
            return {
                "safe": False,
                "reason": f"Dangerous keyword detected: {keyword}",
                "risk_level": "CRITICAL"
            }
    
    # Check for WHERE clause in UPDATE/DELETE
    if ("update" in sql_lower or "delete" in sql_lower) and "where" not in sql_lower:
        return {
            "safe": False,
            "reason": "UPDATE/DELETE without WHERE clause affects all rows",
            "risk_level": "CRITICAL"
        }
    
    return {"safe": True, "risk_level": "LOW"}


@tool
def get_database_schema(target_db: str) -> Dict[str, Any]:
    """Retrieve database schema information"""
    schema = SCHEMA.get(target_db)
    if not schema:
        return {"error": f"Unknown database: {target_db}"}
    
    # Format schema for LLM
    formatted_schema = {}
    for table, info in schema.items():
        formatted_schema[table] = {
            "columns": info.get("columns", []),
            "types": info.get("types", []),
            "relationships": info.get("relationships", {})
        }
    
    return {"schema": formatted_schema, "target_db": target_db}


@tool
def analyze_query_context(nl_query: str, conversation_history: List[Dict]) -> Dict[str, Any]:
    """Analyze query for contextual references"""
    reference_indicators = [
        "same", "previous", "last", "above", "before", "earlier",
        "that", "those", "this", "these", "it", "them"
    ]
    
    query_lower = nl_query.lower()
    has_reference = any(indicator in query_lower for indicator in reference_indicators)
    
    recent_context = []
    if has_reference and conversation_history:
        recent_context = conversation_history[-3:]
    
    return {
        "has_reference": has_reference,
        "recent_context": recent_context,
        "analysis": "Query references previous conversation" if has_reference else "Standalone query"
    }


@tool
def generate_business_hints(operation: str, table: str, target_db: str, nl_query: str) -> List[str]:
    """Generate business logic hints based on query patterns"""
    hints = []
    query_lower = nl_query.lower()
    
    # Performance hints
    if "count" in query_lower and operation == "READ":
        hints.append("Consider adding indexes on frequently queried columns for better performance")
    
    # Business logic hints by database
    if target_db == "hr":
        if "salary" in query_lower:
            if "average" in query_lower:
                hints.append("Consider calculating median salary for better representation")
            if ">" in query_lower or "greater" in query_lower:
                hints.append("Consider creating an index on salary column for range queries")
    
    elif target_db == "healthcare":
        if "appointment" in query_lower and "date" in query_lower:
            hints.append("Consider adding date range filters to avoid loading excessive historical data")
        if "patient" in query_lower and "diagnosis" in query_lower:
            hints.append("Ensure HIPAA compliance when handling patient diagnosis data")
    
    elif target_db == "finance":
        hints.append("Financial data requires extra security and audit logging")
    
    return hints


# ==================== Agent Nodes ====================
class SQLAgentWorkflow:
    def __init__(self):
        self.llm = genai(
            model="gemini-2.5-pro",
            temperature=0.0,
            google_api_key=os.environ.get("GEMINI_API_KEY")
        )
        
        # Create tools list
        self.tools = [
            validate_sql_safety,
            get_database_schema,
            analyze_query_context,
            generate_business_hints
        ]
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_context", self.analyze_context_node)
        workflow.add_node("retrieve_schema", self.retrieve_schema_node)
        workflow.add_node("generate_sql", self.generate_sql_node)
        workflow.add_node("validate_safety", self.validate_safety_node)
        workflow.add_node("generate_hints", self.generate_hints_node)
        workflow.add_node("finalize", self.finalize_node)
        
        # Define edges
        workflow.set_entry_point("analyze_context")
        workflow.add_edge("analyze_context", "retrieve_schema")
        workflow.add_edge("retrieve_schema", "generate_sql")
        workflow.add_edge("generate_sql", "validate_safety")
        workflow.add_conditional_edges(
            "validate_safety",
            self.safety_check_router,
            {
                "safe": "generate_hints",
                "unsafe": "finalize"
            }
        )
        workflow.add_edge("generate_hints", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def analyze_context_node(self, state: AgentState) -> AgentState:
        """Analyze query context and conversation history"""
        context_tool = analyze_query_context.invoke({
            "nl_query": state["nl_query"],
            "conversation_history": state.get("conversation_history", [])
        })
        
        state["metadata"]["context_analysis"] = context_tool
        state["messages"].append(
            SystemMessage(content=f"Context analysis: {context_tool['analysis']}")
        )
        
        return state
    
    def retrieve_schema_node(self, state: AgentState) -> AgentState:
        """Retrieve and format database schema"""
        schema_info = get_database_schema.invoke({"target_db": state["target_db"]})
        
        if "error" in schema_info:
            state["error"] = schema_info["error"]
            return state
        
        state["metadata"]["schema"] = schema_info["schema"]
        
        # Format schema for prompt
        schema_text = self._format_schema_for_prompt(schema_info["schema"])
        state["messages"].append(
            SystemMessage(content=f"Database schema for {state['target_db']}:\n{schema_text}")
        )
        
        return state
    
    def generate_sql_node(self, state: AgentState) -> AgentState:
        """Generate SQL using LLM with structured output"""
        # Build the prompt
        system_prompt = """You are an expert SQL generator. Generate SQL queries based on natural language requests.

Rules:
1. Only use SELECT, INSERT, UPDATE, DELETE operations
2. Never use DROP, TRUNCATE, ALTER, or other DDL statements
3. Use proper JOIN syntax with ON conditions
4. Support aggregations (COUNT, SUM, AVG), GROUP BY, HAVING
5. Support window functions when needed
6. Return valid SQLite-compatible SQL

Respond in this exact JSON format:
{
    "operation": "SELECT|INSERT|UPDATE|DELETE",
    "table": "primary_table_name",
    "sql": "complete SQL statement with semicolon",
    "fields": ["field1", "field2"],
    "joins": ["JOIN clause if needed"],
    "where": "WHERE condition without WHERE keyword",
    "group_by": "GROUP BY fields without keyword",
    "order_by": "ORDER BY clause without keyword",
    "limit": null or integer
}"""
        
        user_message = f"Generate SQL for: {state['nl_query']}"
        
        # Add conversation context if available
        if state["metadata"].get("context_analysis", {}).get("has_reference"):
            recent = state["metadata"]["context_analysis"].get("recent_context", [])
            if recent:
                context_text = "\n".join([
                    f"Previous: {item.get('query', '')} -> {item.get('result', {}).get('sql', '')}"
                    for item in recent
                ])
                user_message += f"\n\nRecent context:\n{context_text}"
        
        messages = state["messages"] + [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            import re
            
            text = response.content
            json_match = re.search(r'(\{.*\})', text, re.S)
            if json_match:
                parsed = json.loads(json_match.group(1))
                
                state["operation"] = parsed.get("operation", "UNKNOWN")
                state["table"] = parsed.get("table", "")
                state["sql"] = parsed.get("sql", "").strip().rstrip(";") + ";"
                state["metadata"].update(parsed)
                
                state["messages"].append(AIMessage(content=f"Generated SQL: {state['sql']}"))
            else:
                state["error"] = "Failed to parse LLM response"
                state["operation"] = "UNKNOWN"
        
        except Exception as e:
            state["error"] = f"SQL generation failed: {str(e)}"
            state["operation"] = "UNKNOWN"
        
        return state
    
    def validate_safety_node(self, state: AgentState) -> AgentState:
        """Validate SQL safety"""
        if state.get("error") or not state.get("sql"):
            return state
        
        safety_check = validate_sql_safety.invoke({"sql": state["sql"]})
        state["metadata"]["safety_check"] = safety_check
        
        if not safety_check["safe"]:
            state["error"] = safety_check["reason"]
            state["metadata"]["risk_level"] = safety_check["risk_level"]
        
        return state
    
    def generate_hints_node(self, state: AgentState) -> AgentState:
        """Generate business hints"""
        hints = generate_business_hints.invoke({
            "operation": state.get("operation", ""),
            "table": state.get("table", ""),
            "target_db": state["target_db"],
            "nl_query": state["nl_query"]
        })
        
        state["business_hints"] = hints
        state["metadata"]["business_hints"] = hints
        
        return state
    
    def finalize_node(self, state: AgentState) -> AgentState:
        """Finalize the result"""
        # Map operation
        if state.get("operation"):
            op_word = state["operation"].upper()
            if op_word == "SELECT":
                state["operation"] = "READ"
            elif op_word == "INSERT":
                state["operation"] = "CREATE"
            elif op_word == "UPDATE":
                state["operation"] = "UPDATE"
            elif op_word == "DELETE":
                state["operation"] = "DELETE"
            else:
                state["operation"] = "UNKNOWN"
        
        # Generate risk assessment for CUD operations
        if state["operation"] in ["CREATE", "UPDATE", "DELETE"]:
            state["risk_assessment"] = self._assess_risk(state)
        
        return state
    
    def safety_check_router(self, state: AgentState) -> str:
        """Route based on safety check"""
        if state.get("error"):
            return "unsafe"
        
        safety = state["metadata"].get("safety_check", {})
        return "safe" if safety.get("safe", False) else "unsafe"
    
    def _format_schema_for_prompt(self, schema: Dict) -> str:
        """Format schema for LLM prompt"""
        lines = []
        for table, info in schema.items():
            cols = info.get("columns", [])
            types = info.get("types", [])
            col_defs = [f"{col} ({types[i]})" for i, col in enumerate(cols) if i < len(types)]
            lines.append(f"{table}: {', '.join(col_defs)}")
            
            rels = info.get("relationships", {})
            for col, ref in rels.items():
                lines.append(f"  → {col} references {ref}")
        
        return "\n".join(lines)
    
    def _assess_risk(self, state: AgentState) -> Dict[str, Any]:
        """Assess operation risk"""
        sql = state.get("sql", "").lower()
        operation = state.get("operation", "")
        target_db = state.get("target_db", "")
        
        risk_level = "LOW"
        risk_factors = []
        
        if operation == "DELETE":
            risk_level = "HIGH"
            risk_factors.append("DELETE operation - data will be permanently removed")
        
        if "where" not in sql and operation in ["UPDATE", "DELETE"]:
            risk_level = "CRITICAL"
            risk_factors.append("No WHERE clause - affects all rows")
        
        if target_db in ["finance", "healthcare"]:
            risk_factors.append(f"{target_db.title()} data - high sensitivity")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
        
        return {
            "level": risk_level,
            "factors": risk_factors
        }


# ==================== Main Interface ====================
# Global workflow instance
_workflow_instance = None
_conversation_history = []

def get_workflow():
    """Get or create workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = SQLAgentWorkflow()
    return _workflow_instance


def llm_parse_to_action(nl_text: str, target_db: str = "hr") -> Dict[str, Any]:
    """
    Main entry point - compatible with existing interface
    """
    workflow = get_workflow()
    
    # Initialize state
    initial_state = AgentState(
        messages=[],
        nl_query=nl_text,
        target_db=target_db,
        operation=None,
        table=None,
        sql=None,
        metadata={},
        error=None,
        conversation_history=_conversation_history.copy(),
        business_hints=[],
        risk_assessment={}
    )
    
    # Run the graph
    final_state = workflow.graph.invoke(initial_state)
    
    # Build response
    result = {
        "operation": final_state.get("operation", "UNKNOWN"),
        "table": final_state.get("table", ""),
        "sql": final_state.get("sql"),
        "metadata": final_state.get("metadata", {}),
        "target_db": target_db
    }
    
    # Add business hints
    if final_state.get("business_hints"):
        result["metadata"]["business_hints"] = final_state["business_hints"]
    
    # Add risk assessment
    if final_state.get("risk_assessment"):
        result["metadata"]["risk_assessment"] = final_state["risk_assessment"]
    
    # Add error if present
    if final_state.get("error"):
        result["metadata"]["error"] = final_state["error"]
        result["operation"] = "UNKNOWN"
    
    # Update conversation history
    _conversation_history.append({
        "timestamp": datetime.now().isoformat(),
        "query": nl_text,
        "result": result,
        "target_db": target_db
    })
    
    # Keep only recent history
    if len(_conversation_history) > 10:
        _conversation_history[:] = _conversation_history[-10:]
    
    return result


# For compatibility
CONVERSATION_HISTORY = _conversation_history