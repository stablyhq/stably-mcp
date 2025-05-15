# Stably MCP
This MCP server enables clients like Cursor to create end-to-end tests using Stably's testing platform. The magic happens when MCP uses the codebase as context and embeds such knowledge implicitly to test steps generated. It can even save explicit knowledge to the Stably backend to help test execution. 

## How to install
1. Clone or download this repository to your local machine.
2. Ensure you have Python 3.10 or higher installed.
3. Install the dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv
   uv pip install -r requirements.txt
   ```
4. Then, if you are using Cursor, go to "Settings", "Cursor Settings", "MCP", "Add new global MCP server", and use following setting:

```json
{
  "mcpServers": {
    "Stably end-to-end testing agent": {
      "command": "python3",
      "args": [
        "/path/StablyMCP/main.py"
      ],
      "env": {
        "API_BASE_URL": "https://app.stably.ai/api/trpc", 
        "AUTH_BASE_URL": "https://65218409992.propelauthtest.com",
        "AUTH_EMAIL": "your-account@example.com",
        "AUTH_PASSWORD": "XXXXXXXXXXXX",
      }
    }
  }
}
```
Note: if you want to run it on production, simply remove API_BASE_URL and AUTH_BASE_URL.

### How does it work?

The Stably MCP server provides a bridge between an MCP client (e.g., Cursor) and Stably's testing platform:

1. The MCP server exposes several functions that Cursor can call:
   - Set testing URL and account information
   - Create end-to-end tests with AI-generated test steps
   - Save knowledge about UX designs, user flows, and preferences

2. When you create a test through a client, the MCP server:
   - Authenticates with the Stably API
   - Uses the codebase context to generate appropriate test steps
   - Extract and upload knowledge from the codebase to Stably's backend
   - Returns the URL where you can review 

3. The magic happens when MCP server captures important knowledge from the codebase and uses it to generate better tests and even help the tests to run more effectively.

### Limitations

Current known limitations include:

1. **Local Development Testing**: When testing local apps from remote server, proper tunneling is required. One experimental feature is to use to set the `NGROK_ENABLED=true` and `NGROK_AUTH_TOKEN` environment variables if testing against localhost. But this feature is highly unstable and not tested, and therefore not recommended.

2. **Test Step Generation**: The quality of generated test steps depends on the codebase context and the clarity of test descriptions. It will not know dynamic context such as A/B tests with dynamic feature flags. Also, be specific when describing test scenarios but do not force AI to be overly specific, otherwise the test might be flaky.

3. **Authentication**: For applications requiring login, you'll need to provide testing account credentials using the appropriate MCP functions.

4. **TBD**: more limitations may be added later

