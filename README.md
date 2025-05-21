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
        "AUTH_EMAIL": "your-account@example.com",
        "AUTH_PASSWORD": "XXXXXXXXXXXX",
      }
    }
  }
}
```

### How to use Stably MCP?
1. If you see a green dot next to the MCP server 'Stably end-to-end testing agent', instead of a red dot or orange dot, then it is correctly installed
<img width="951" alt="image" src="https://github.com/user-attachments/assets/56d05e47-1b46-4e62-a28b-7703545e0903" />

2. If you encounter any issues, e.g., login expired, try to "refresh" it and it should fix most issues. Otherwise, contact the Stably AI team
<img width="951" alt="image" src="https://github.com/user-attachments/assets/05e509d4-0505-47d0-b917-9db25d59feb7" />

3. It is recommended to use "Agent" model with "claude-3.7-sonnet" as it is the most tested setting, other settings might also work if you know what you are doing
<img width="658" alt="image" src="https://github.com/user-attachments/assets/d456ff82-b31d-498b-a407-2ccb5ae267bd" />

4. The Stably MCP works on your default project, if you want it to work with another project, you can switch your project on Stably App and "refresh" the Stably MCP on Cursor

5. Start by asking the AI "how to use Stably MCP?" and you should see it calling "get_user_tutorial" tool, which should then provide you more detailed instructions

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

1. **Local Development Testing**: When testing local apps from remote server, proper tunneling is required. One experimental feature is to set the `NGROK_ENABLED=true` and `NGROK_AUTH_TOKEN` environment variables if testing against localhost. But this feature is highly unstable and not tested, and therefore not recommended.

2. **No access to runtime execution**: The quality of generated test steps depends on the codebase context and the clarity of test descriptions. It will not know dynamic context such as A/B tests with dynamic feature flags. 

3. **Context Limit**: Currently AI is still constrained by context length and sometimes a little bit "lazy" and does not want to explore everything if you simply say a high level prompt like "explore the codebase and build knowledge base for every useful detail", or if you want to "create 20 QA tests for my codebase" in a single request, it will also not provide you high quality results. It works better if you have more specific things in mind and the AI has fewer things to digest and generate.

4. **TBD**: more limitations may be added later

