# Model Context Protocol (MCP)

MCP is an open protocol for exposing tools and data to models through a standard
server interface. The Agents SDK can consume an MCP server: MCPServerStdio spawns a
local server process and speaks to it over stdio, while HostedMCPTool points at an
already-deployed remote server by URL. A connected server's tools appear to the
agent alongside its native function tools. This project ships its own stdio MCP
server exposing list_docs and docs_lookup.
