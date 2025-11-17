#!/usr/bin/env python3
"""
Test script to verify agent tools work correctly.
"""

from openai import OpenAI
from sqlmodel import Session, create_engine
from core.agent import LLMAgent
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables

# Setup
print("=== Testing Agent Tools ===\n")

engine = create_engine("sqlite:///database.db")
create_db_and_tables()
session = Session(engine)

# Initialize LLM client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# Initialize agent
db_manager = DatabaseManager(session)
agent = LLMAgent(client, db_manager)

print("1. Testing find_component_file tool...")
result = agent._find_component_file({"component_name": "loss"})
print(f"   Result: {result}")

print("\n2. Testing get_full_file tool...")
# First find the file path
file_result = agent._find_component_file({"component_name": "loss"})
if "result" in file_result and file_result["result"]:
    filepath = file_result["result"][0]
    print(f"   Found file: {filepath}")

    # Now get the full file
    full_file_result = agent._get_full_file({"filepath": filepath})
    print(f"   Full file result: {full_file_result.get('error', 'Success')}")
    if "result" in full_file_result:
        print(
            f"   File summary length: {len(full_file_result['result'][0].text)} characters"
        )
else:
    print("   Could not find file path for 'loss'")

print("\n3. Testing search_components tool...")
search_result = agent._search_components({"keyword": "loss", "limit": 3})
print(f"   Search result: {len(search_result.get('result', []))} components found")

print("\n✅ Tool testing complete!")
