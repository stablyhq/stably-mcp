# Stably MCP description
STABLY_MCP_DESCRIPTION = """
Stably MCP (model context protocol) is a tool that helps you to create end-to-end QA tests for your application.
It uses your whole codebase as context to create tests and set knowledge for running the tests.
"""


# User tutorial
USER_TUTORIAL_TOOL_DESCRIPTION = STABLY_MCP_DESCRIPTION + """
Use this tool when user don't know how to use Stably MCP.

Usage:
* This tool is used to get the best practices of using Stably MCP.
* You should first explore the codebase (e.g., find a README.md) to understand theirapplication
* Then, you can give user 3-5 customized suggestions on how to use Stably MCP to create a test or how to set knowledge.
* Format your examples as quoted text in markdown.
"""

USER_TUTORIAL = """
Best practices to use Stably MCP:
1. Stably works the best with knowledge-based testing, and there are three types of knowledge: uncommon UX design, basic user flows, and user preferences.
2. Whenever possible, explicitly ask Cursor to learn your codebase and set as much knowledge as possible to get the most reliable testing experience.
3. Be specific about the test you want to create, but don't force AI to be overly specific which makes your test flaky.
4. After AI has created a test, ask AI to set knowledge especially for the test you just created.

For example, you can ask Stably MCP to create following tests:
{suggested_qa_tests_to_create}

Or, you can ask Stably MCP to explore and build knowledge for your tests.
{suggested_knowledge_to_set}
"""

# Knowledge

KNOWLEDGE_COMMON_FORMAT = "Each knowledge should be multiple sentences to describe: 1. when does the knowledge apply and 2. what's special about it."


GOTCHA_KNOWLEDGE_REQUIREMENTS = f"""
Requirements:
* {KNOWLEDGE_COMMON_FORMAT}
* You don't need to save any common sense knowledge, just save the uncommon UX design that are not obvious to you.
* Formally, if there exists a path A->B->C, but the path from A -> B is not obvious and might cause you to fail to reach C. Save the knowledge necessary to help you to reach C.
"""

USAGE_KNOWLEDGE_REQUIREMENTS = f"""
Requirements:
* {KNOWLEDGE_COMMON_FORMAT}
* Whenever you found a common pattern or a common user usage scenario to use the application, save it here.
* This knowledge is helpful to evaluate test coverage and make test planning suggestions.
"""

PREFERENCE_KNOWLEDGE_REQUIREMENTS = f"""
Requirements:
* {KNOWLEDGE_COMMON_FORMAT}
* Use this tool to set user preferences when user explicitly ask you to remember something, or when user complain about something.
"""

KNOWLEDGE_WARNING = f"""
Warning:
* Knowledge should only be visual-based, and never include any knowledge that is not visual-based.
* Don't include low-level technical details that are not exposed to a normal user.
* Don't include any information about development, deployment, or any other details that the daily user would not care about.
"""

KNOWLEDGE_SAVED_RESPONSE = """
Congratulation! Knowledge set! {updates} knowledge updates have been made.
Here's a link where user can review the knowledge: {url}
You MUST ALWAYS provide a clickable link using markdown to the user so they can review the knowledge.
For example, show it like this: [Click here to review the knowledge I just set](https://app.stably.ai/project/XXXXXXXXXXX/knowledge?tab=manual)
"""

# Setup
TESTING_ACCOUNT_TOOL_DESCRIPTION = """
Set testing account information

Usage: 
* If testing the codebase requires a testing account, ask the user to provide the testing account first, then call this tool to set the testing account.
"""

TESTING_URL_TOOL_DESCRIPTION = """
Saving testing URL

Usage:
* You should never make any assumptions about the testing URL, always ask the user to provide the testing URL.
* If testing this codebase requires a testing account, set may_need_a_testing_account to True
"""

INVALID_URL = """
Your URL is not valid and has not been saved.
"""

STOP_AND_GET_URL = """
Stop! You did not provide a testing URL. Politely ask the user to provide the testing URL first, and then call set_testing_url tool to set the testing URL.
"""

TESTING_URL_UPDATED = """
Congratulation! Testing URL updated! You can now working on the actual testing
"""

TESTING_ACCOUNT_UPDATED = """
Congratulation! Testing account updated! You can now working on the actual testing
"""

URL_SAVED_AND_GET_TESTING_ACCOUNT = """
Congratulations! Testing URL saved! 
Now, you need to provide a testing account to test this application. 
Please ask the user to provide the testing account and then call set_testing_account tool to set the testing account.
"""

STOP_AND_GET_TESTING_ACCOUNT = """
Stop! You did not provide a testing account. Use set_testing_account tool to set the testing account first.
"""

# Test creation
TEST_CREATION_TOOL_DESCRIPTION = """
Create a new end‑to‑end QA test

Usage:
* We are creating a QA test, so describe the test in a way to describe how normal users would do.
* Each test step should be a paragraph containing description of multiple actions and expected result.
* Always rollback the data changes at the end of the test so that you can rerun the test again.
"""

STOP_AND_GET_TESTING_URL = """
Stop and don't call anything else! Politely ask the user to provide the testing URL.
"""

TEST_CREATED_RESPONSE = """
1. I created a new end‑to‑end test. The test URL is {test_url}. 
   You must share this URL in markdown so the user can click the link to review the test.
   For example, show it like this: [Click here to review the test](https://test-url.com)
2. If you think the test requires more knowledge for execution, go get it!
   You don't need to confirm with user but go straight to extract more knowledge from the codebase and set such knowledge yourself.
3. If you are not sure about whether more knowledge is needed, you can recommend the user to set more knowledge.
   For example, you can ask your if user want to set their preference on how they want to run the test (e.g. be optimistic or pessimistic, wait shorter between each action, etc.)
   You can also ask user if they want you to explore and set uncommon UX design that might help you to run the test you just created.
   Further, you can ask user if they want you to explore and set basic user flows that might help you to run other test more reliably.
4. Use the following tools to set knowledge:
   - set_uncommon_ux_designs
   - set_basic_user_flows
   - set_user_preferences
5. After you have set all the knowledge you need, share the clickable link again so the user can review the test.
"""