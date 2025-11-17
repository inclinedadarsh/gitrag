from utils.json_builder import (
    build_summary_id,
    build_component_metadata,
    extract_file_summary_id,
    extract_component_id_from_mapping,
    build_dependency_relationship,
    build_code_mapping_data,
    build_summary_data,
    normalize_filepath,
    extract_module_name_from_filepath,
)

# Test build_summary_id
print("=== Testing build_summary_id ===")
print(f"Repository: {build_summary_id('repository', 'my-project')}")
print(f"File: {build_summary_id('file', 'auth/login.py')}")
print(f"Function: {build_summary_id('function', 'authenticate_user')}")
print(f"File with type: {build_summary_id('file', 'auth/login.py', 'compact')}")

# Test extract_file_summary_id
print("\n=== Testing extract_file_summary_id ===")
print(f"auth/login.py → {extract_file_summary_id('auth/login.py')}")
print(f"docs/README.md → {extract_file_summary_id('docs/README.md')}")
print(
    f"inclinet/neural_network.py → {extract_file_summary_id('inclinet/neural_network.py')}"
)

# Test extract_component_id_from_mapping
print("\n=== Testing extract_component_id_from_mapping ===")
print(
    f"authenticate_user + function → {extract_component_id_from_mapping('authenticate_user', 'function')}"
)
print(
    f"AuthManager + class → {extract_component_id_from_mapping('AuthManager', 'class')}"
)

# Test build_component_metadata
print("\n=== Testing build_component_metadata ===")
metadata = build_component_metadata(
    name="authenticate_user",
    element_type="function",
    signature="authenticate_user(username: str, password: str) -> bool",
    docstring="Validates user credentials against database",
    line_start=15,
    line_end=30,
)
print(f"Component metadata: {metadata}")

# Test build_dependency_relationship
print("\n=== Testing build_dependency_relationship ===")
dep = build_dependency_relationship("func_login", "func_authenticate", "calls")
print(f"Dependency: {dep}")

# Test build_code_mapping_data
print("\n=== Testing build_code_mapping_data ===")
mapping = build_code_mapping_data(
    summary_id="func_authenticate_user",
    filepath="auth/login.py",
    line_start=15,
    line_end=30,
    element_type="function",
    content_preview="def authenticate_user(username: str, password: str) -> bool:",
)
print(f"Code mapping: {mapping}")

# Test build_summary_data
print("\n=== Testing build_summary_data ===")
summary = build_summary_data(
    summary_id="func_authenticate_user",
    level="function",
    text="Validates user credentials against database using bcrypt",
    token_count=8,
    parent_id="file_auth_login_py",
    target_id="authenticate_user",
    metadata={"complexity": "medium"},
)
print(f"Summary data: {summary}")

# Test normalize_filepath
print("\n=== Testing normalize_filepath ===")
print(r"\auth\login.py → " + normalize_filepath(r"\auth\login.py"))
print("/auth/login.py → " + normalize_filepath("/auth/login.py"))

# Test extract_module_name_from_filepath
print("\n=== Testing extract_module_name_from_filepath ===")
print(
    f"inclinet/neural_network.py → {extract_module_name_from_filepath('inclinet/neural_network.py')}"
)
print(
    f"examples/fizzbuzz.py → {extract_module_name_from_filepath('examples/fizzbuzz.py')}"
)

print("\n=== All tests completed! ===")
