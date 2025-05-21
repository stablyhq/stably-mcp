from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from fastmcp import FastMCP, Context
import os
import asyncio
from typing import List, Optional
import aiohttp
import ngrok
from dotenv import load_dotenv
from lib.stably_api import StablyAPI
from lib.auth import StablyAuth
from lib import prompt

load_dotenv()
NGROK_ENABLED = os.environ.get("NGROK_ENABLED", "false").lower() == "true"

@dataclass
class AppContext:
    api: StablyAPI
    testing_url: Optional[str] = None
    testing_account: Optional[str] = None
    may_need_a_testing_account: Optional[bool] = False

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type‑safe context."""
    auth = StablyAuth(os.getenv("AUTH_BASE_URL", "https://auth.stably.ai"))
    auth_token, active_org_id = await auth.authenticate(
        os.getenv("AUTH_EMAIL"), os.getenv("AUTH_PASSWORD")
    )
    stably_api = StablyAPI(
        os.getenv("API_BASE_URL", "https://app.stably.ai") + "/api/trpc", auth_token, active_org_id
    )

    if NGROK_ENABLED:
        ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))

    try:
        yield AppContext(api=stably_api)
    finally:
        if NGROK_ENABLED:
            await kill_listeners()

mcp = FastMCP(
    name="Stably End‑to‑End Test Creator",
    description=prompt.STABLY_MCP_DESCRIPTION,
    lifespan=app_lifespan,
)

async def kill_listeners():
    """Close all ngrok tunnels via the 4040 API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:4040/api/tunnels") as resp:
                data = await resp.json()
                tunnels = data.get("tunnels", [])
                await asyncio.gather(
                    *[
                        session.delete(f"http://127.0.0.1:4040/api/tunnels/{t['name']}")
                        for t in tunnels
                    ]
                )
    except Exception:
        pass

@mcp.tool(description=prompt.USER_TUTORIAL_TOOL_DESCRIPTION)
async def get_user_tutorial(suggested_qa_tests_to_create: List[str], suggested_knowledge_to_set: List[str]) -> str:
    return prompt.USER_TUTORIAL.format(
        suggested_qa_tests_to_create='\n'.join(suggested_qa_tests_to_create),
        suggested_knowledge_to_set='\n'.join(suggested_knowledge_to_set)
    )

@mcp.tool(description=prompt.TESTING_URL_TOOL_DESCRIPTION)
async def set_testing_url(ctx: Context, user_provided_url: str, may_need_a_testing_account: bool) -> str:
    # check if user_provided_url is provided
    if not user_provided_url:
        return prompt.STOP_AND_GET_URL
    # verify if user_provided_url is a valid url
    if not (user_provided_url.startswith("http://") or user_provided_url.startswith("https://")):
        return prompt.INVALID_URL
    ctx.request_context.lifespan_context.testing_url = user_provided_url
    ctx.request_context.lifespan_context.may_need_a_testing_account = may_need_a_testing_account
    api = ctx.request_context.lifespan_context.api
    await api.set_testing_url_knowledge(user_provided_url, may_need_a_testing_account)
    if may_need_a_testing_account and not ctx.request_context.lifespan_context.testing_account:
        return prompt.URL_SAVED_AND_GET_TESTING_ACCOUNT
    return prompt.TESTING_URL_UPDATED

@mcp.tool(description=prompt.TESTING_ACCOUNT_TOOL_DESCRIPTION)
async def set_testing_account(ctx: Context, testing_account: str) -> str:
    ctx.request_context.lifespan_context.testing_account = testing_account
    api = ctx.request_context.lifespan_context.api
    if ctx.request_context.lifespan_context.testing_url:
        await api.set_testing_account_knowledge(testing_account, ctx.request_context.lifespan_context.testing_url)
    else:
        await api.set_testing_account_knowledge(testing_account)
    return prompt.TESTING_ACCOUNT_UPDATED

@mcp.tool(description=prompt.TEST_CREATION_TOOL_DESCRIPTION)
async def add_e2e_test(ctx: Context,
                       multi_step_test_description: List[str]) -> str:
    api = ctx.request_context.lifespan_context.api

    # get existing knowledge
    existing_knowledge = await asyncio.gather(*[api.retrieve_testing_urls(), api.retrieve_testing_account_knowledge()])
    # check if testing url is provided 
    existing_testing_urls, existing_testing_account_knowledge = existing_knowledge
    if existing_testing_urls:
        url = existing_testing_urls[-1]
    elif ctx.request_context.lifespan_context.testing_url:
        url = ctx.request_context.lifespan_context.testing_url
        may_need_a_testing_account = ctx.request_context.lifespan_context.may_need_a_testing_account
        await api.set_testing_url_knowledge(ctx.request_context.lifespan_context.testing_url, may_need_a_testing_account)
    else:
        return prompt.STOP_AND_GET_TESTING_URL

    # if testing account is needed, check if it is provided
    if not existing_testing_account_knowledge and ctx.request_context.lifespan_context.may_need_a_testing_account:
        return prompt.STOP_AND_GET_TESTING_ACCOUNT
        
    if NGROK_ENABLED and ("localhost" in url or "127.0.0.1" in url):
        await kill_listeners()
        listener = await ngrok.forward(url)
        url = listener.url()

    
    test_url = await api.add_e2e_test(url, "\n".join(multi_step_test_description))
    return prompt.TEST_CREATED_RESPONSE.format(test_url=test_url)


@mcp.tool(description=f"{prompt.GOTCHA_KNOWLEDGE_REQUIREMENTS}\n{prompt.KNOWLEDGE_WARNING}")
async def set_uncommon_ux_designs(ctx: Context, list_of_uncommon_ux_designs: List[str]) -> str:
    api = ctx.request_context.lifespan_context.api
    updated_count = await api.set_uncommon_ux_designs(list_of_uncommon_ux_designs)
    knowledge_url = await api.get_knowledge_url()
    return prompt.KNOWLEDGE_SAVED_RESPONSE.format(updates=updated_count, url=knowledge_url)

@mcp.tool(description=f"{prompt.USAGE_KNOWLEDGE_REQUIREMENTS}\n{prompt.KNOWLEDGE_WARNING}")
async def set_basic_user_flows(ctx: Context, list_of_basic_user_flows: List[str]) -> str:
    api = ctx.request_context.lifespan_context.api
    updated_count = await api.set_basic_user_flows(list_of_basic_user_flows)
    knowledge_url = await api.get_knowledge_url()
    return prompt.KNOWLEDGE_SAVED_RESPONSE.format(updates=updated_count, url=knowledge_url)

@mcp.tool(description=f"{prompt.PREFERENCE_KNOWLEDGE_REQUIREMENTS}\n{prompt.KNOWLEDGE_WARNING}")
async def set_user_preferences(ctx: Context, list_of_user_preferences: List[str]) -> str:
    api = ctx.request_context.lifespan_context.api
    updated_count = await api.set_user_preferences(list_of_user_preferences)
    knowledge_url = await api.get_knowledge_url()
    return prompt.KNOWLEDGE_SAVED_RESPONSE.format(updates=updated_count, url=knowledge_url)

if __name__ == "__main__":
    mcp.run()