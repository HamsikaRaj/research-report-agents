# Function tools

The @function_tool decorator turns a Python function into a tool the model can call.
It builds a JSON schema from the function's type hints and docstring, and validates
the model's arguments (often Pydantic models) before the function runs. Setting
needs_approval=True makes a tool require human approval: the run pauses as an
interruption until the host application approves or rejects the call.
