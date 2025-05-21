import aiohttp
from pydantic import BaseModel
from urllib.parse import urlparse
from typing import List, Optional
import json
from urllib.parse import urlencode
import logging
import os
from enum import Enum
import asyncio
import re

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'stably_api.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'
)
logger = logging.getLogger('stably_api')

class CreateTestDraftResponse(BaseModel):
    id: str

class PublishTestDraftResponse(BaseModel):
    testId: str

class KnowledgeItem(BaseModel):
    id: str
    content: str

class KnowledgeType(Enum):
    GOTCHA = "Uncommon UX Design"
    USAGE = "Basic User Flows"
    PREFERENCE = "User Preferences"

class StablyAPI:
    def __init__(self, api_base_url: str, auth_token: str, active_org_id: str):
        self.auth_token = auth_token
        self.active_org_id = active_org_id
        self.API_BASE_URL = api_base_url
        self.__PROJECT_ID = None
        parsed_url = urlparse(api_base_url)
        self.DOMAIN = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if not self.API_BASE_URL:
            raise Exception("API_BASE_URL must be set")
        
    async def get_or_set_project_id(self) -> str:
        if not self.__PROJECT_ID:
            self.__PROJECT_ID = await self._get_default_project_id()
        return self.__PROJECT_ID
    
    async def __call_trpc_query(self, endpoint: str, args: dict) -> dict:
        # Prepare the request URL and headers
        url = f"{self.API_BASE_URL}/{endpoint}?batch=1"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        # Format the input parameter according to the example URL
        input_param = {
            "0": {
                "json": args
            }
        }
        logger.info(f"Calling {url} with input {input_param}")
        async with aiohttp.ClientSession() as session:
         
            full_url = f"{url}&{urlencode({'input': json.dumps(input_param)})}"
            async with session.get(full_url, headers=headers) as response:
                response.raise_for_status()
                json_response = await response.json()
                logger.info(f"Query Response: {json_response}")
                return json_response
    
    async def __call_trpc_mutation(self, endpoint: str, args: dict) -> dict:
        # Prepare the request URL and headers
        url = f"{self.API_BASE_URL}/{endpoint}?batch=1"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "0": {
                "json": args
            }
        }
        logger.info(f"Calling {url} with payload {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                json_response = await response.json()
                logger.info(f"Mutation Response: {json_response}")
                return json_response
            
    async def _get_default_project_id(self) -> str:
        response = await self.__call_trpc_query("project.getDefaultProject", {
            "teamId": self.active_org_id,
        })
        return response[0]['result']['data']['json']['id']
    
    async def _list_knowledge(self) -> List[KnowledgeItem]:
        project_id = await self.get_or_set_project_id()
        response = await self.__call_trpc_query("knowledge.list", {
            "projectId": project_id,
        })
        obj = response[0]['result']['data']['json']
        return [KnowledgeItem(**item) for item in obj]
 
    async def _create_knowledge(self, knowledge_content: str) -> bool:
        project_id = await self.get_or_set_project_id()
        existing_knowledge = await self._list_knowledge()
        # check if the knowledge item already exists
        if any(item.content == knowledge_content for item in existing_knowledge):
            return True
        new_index = len(existing_knowledge)
        logger.info(f"Creating knowledge item with index {new_index}")
        await self.__call_trpc_mutation("knowledge.createManualKnowledge", {
            "projectId": project_id,
            "content": knowledge_content,
            "order": new_index,
        })
        return True

    async def _delete_knowledge(self, knowledge_id: str) -> bool:
        project_id = await self.get_or_set_project_id()
        await self.__call_trpc_mutation("knowledge.deleteKnowledgeItem", {
            "knowledgeItemId": knowledge_id,
            "projectId": project_id,
        })
        return True
    
    async def _update_knowledge(self, knowledge_id: str, new_knowledge: str) -> bool:
        project_id = await self.get_or_set_project_id()
        await self.__call_trpc_mutation("knowledge.updateManualKnowledge", {
            "knowledgeItemId": knowledge_id,
            "projectId": project_id,
            "content": new_knowledge,
        })
        return True
    
    async def _query_knowledge(self, query: str, top_k: Optional[int] = None) -> List[KnowledgeItem]:
        project_id = await self.get_or_set_project_id()
        params = {
            "query": query,
            "projectId": project_id
        }
        if top_k:
            params["topK"] = top_k
        response = await self.__call_trpc_mutation("knowledge.query", params)
        obj = response[0]['result']['data']['json']
        return [KnowledgeItem(**item) for item in obj]
    
    async def _create_test_draft(self, url: str) -> CreateTestDraftResponse:
        project_id = await self.get_or_set_project_id()
        logger.info(f"Calling testDraft.createTestDraft with payload {url}")
        response = await self.__call_trpc_mutation("testDraft.createTestDraft", {
            "projectId": project_id,
            "runOnMobile": False,
            "testType": "WEB",
            "websiteUnderTest": url,
        })
        data = response[0]['result']['data']['json']
        return CreateTestDraftResponse(**data)

    async def _add_project_website(self, url: str) -> bool:
        project_id = await self.get_or_set_project_id()
        await self.__call_trpc_mutation("project.addProjectWebsite", {
            "projectId": project_id,
            "url": url,
        })
        return True
    
    async def _add_ai_steps(self, test_content_id: str, prompt: str) -> bool:
        payload = {
            "testContentId": test_content_id,
            "stepPrompt": "You are a test automation engineer. You are given a prompt and you need to create a test step for the prompt. Note that the navigation steps are already included, so you don't need to generate them.",
            "mode": "override",
            "uploadedFiles": {
                "mainScript": {
                    "content": prompt,
                    "name": "new_test.txt"
                },
                "libraryFiles": []
            }
        }
        
        await self.__call_trpc_mutation("testContent.addNewAISteps", payload)
        return True
    
    async def _generate_test_name(self, test_content_id: str) -> bool:
        await self.__call_trpc_mutation("test.generateTestName", {
            "testContentId": test_content_id,
        })
        return True
    
    async def _publish_test_draft(self, test_content_id: str) -> PublishTestDraftResponse:
        result = await self.__call_trpc_mutation("testDraft.publishTestDraft", {
            "testContentId": test_content_id,
        })
        return PublishTestDraftResponse(**result[0]['result']['data']['json'])
    
    async def _build_test_knowledge(self, test_content_id: str) -> bool:
        project_id = await self.get_or_set_project_id()
        await self.__call_trpc_mutation("testDraft.buildTestKnowledge", {
            "projectId": project_id,
            "testId": test_content_id,
        })
        return True
    
    async def _create_recorder_room(self) -> str:
        project_id = await self.get_or_set_project_id()
        response = await self.__call_trpc_mutation("recorder.createRoom", {
            "projectId": project_id,
        })
        room_name = response[0]['result']['data']['json']
        return room_name
    
    async def _start_recording(self, room_name: str, test_content_id: str) -> bool:
        await self.__call_trpc_mutation("recorder.start", {
            "roomName": room_name,
            "testContentId": test_content_id,
            "driverType": "browser"
        })
        return True

    async def set_testing_account_knowledge(self, testing_account_information: str, testing_url: Optional[str] = None) -> int:
        url_info = f" for the following url: {testing_url}" if testing_url else ""
        testing_account_knowledge = f"User provided testing account information{url_info}, which could be used for login: {testing_account_information}"
        return await self._set_knowledge([testing_account_knowledge], KnowledgeType.PREFERENCE, ["StablyMCP"])
    
    async def set_testing_url_knowledge(self, testing_url: str, may_need_a_testing_account: bool) -> int:
        testing_url_knowledge = f"User provided a testing url: {testing_url}, testing this url {'does not' if not may_need_a_testing_account else ''} require a testing account"
        return await self._set_knowledge([testing_url_knowledge], KnowledgeType.PREFERENCE, ["StablyMCP"])
    
    async def retrieve_testing_account_knowledge(self, testing_url: Optional[str] = None) -> List[KnowledgeItem]:
        query = "Recall any information about the testing account"
        if testing_url:
            query += f" for the following url: {testing_url}"
        testing_account_knowledge = await self._query_knowledge(query, 1)
        return testing_account_knowledge
    
    async def retrieve_testing_urls(self) -> List[str]:
        query = "Recall knowledge about the testing url for this project. Note it has to be a valid testing url, startswith http or https."
        testing_url_knowledge = await self._query_knowledge(query, 3)
        urls = []
        for each in testing_url_knowledge:
            # use regex to match a url
            valid_url = re.search(r'https?://\S+', each.content)
            if valid_url:
                urls.append(valid_url.group(0))
        logging.info(f"Retrieved testing url: {urls}")
        return urls
    
    async def _set_knowledge(self, knowledge_contents: List[str], type: KnowledgeType, hashtag: List[str]) -> int:
        processed_knowledge_contents = []
        logger.info(f"Setting knowledge of type {type} with contents {knowledge_contents}")
        for each in knowledge_contents:
            single_knowledge = f"[{type.value}] {each}"
            if hashtag:
                single_knowledge += f" #{'#'.join(hashtag)}"
            processed_knowledge_contents.append(single_knowledge)
        knowledge = '\n'.join(processed_knowledge_contents)
        duplicate_query = f"Retrieve all knowledge items that are duplicates to the following knowledge: {knowledge}"
        conflict_query = f"Retrieve all knowledge items that are conflicting with the following knowledge: {knowledge}"

        duplicate_knowledge, conflict_knowledge = await asyncio.gather(
            self._query_knowledge(duplicate_query),
            self._query_knowledge(conflict_query)
        )
        knowledge_to_delete = set([item.id for item in conflict_knowledge + duplicate_knowledge])
        logger.info(f"Deleting {len(knowledge_to_delete)} knowledge items...")
        logger.info(f"Creating {len(processed_knowledge_contents)} knowledge items...")
        delete_tasks = [self._delete_knowledge(item_id) for item_id in knowledge_to_delete]
        create_tasks = [self._create_knowledge(each) for each in processed_knowledge_contents]
        await asyncio.gather(*delete_tasks, *create_tasks)
        return len(delete_tasks) + len(create_tasks)
    
    async def set_uncommon_ux_designs(self, list_of_uncommon_ux_designs: List[str]) -> int:
        return await self._set_knowledge(list_of_uncommon_ux_designs, KnowledgeType.GOTCHA, ["StablyMCP"])
    
    async def set_basic_user_flows(self, list_of_basic_user_flows: List[str]) -> int:
        return await self._set_knowledge(list_of_basic_user_flows, KnowledgeType.USAGE, ["StablyMCP"])
    
    async def set_user_preferences(self, list_of_user_preferences: List[str]) -> int:
        return await self._set_knowledge(list_of_user_preferences, KnowledgeType.PREFERENCE, ["StablyMCP"])
     
    async def get_knowledge_url(self) -> str:
        project_id = await self.get_or_set_project_id()
        return f"{self.DOMAIN}/project/{project_id}/knowledge?tab=manual"
    
    async def add_e2e_test(self, url: str, prompt: str, publish: bool = False) -> str:
        project_id = await self.get_or_set_project_id()
        # 1. create a new test draft
        test_draft = await self._create_test_draft(url)
        # 2. add the project website
        await self._add_project_website(url)
        # 3. create a new step
        await self._add_ai_steps(test_draft.id, prompt)
        # 4. generate a test name
        await self._generate_test_name(test_draft.id)
        if publish:
            # 5. publish the test, and build test knowledge
            published_test = await self._publish_test_draft(test_draft.id)
            # 6. build test knowledge
            await self._build_test_knowledge(published_test.testId)
            # prepare the test
            test_url = f"{self.DOMAIN}/project/{project_id}/test/{published_test.testId}"
        else:
            # prepare the test
            test_url = f"{self.DOMAIN}/project/{project_id}/testDraft/{test_draft.id}"
        return test_url
