import json
import aiohttp

class StablyAuth:
    def __init__(self, auth_base_url: str):
        if not auth_base_url:
            raise Exception('AUTH_BASE_URL is not set')
        self.AUTH_BASE_URL = auth_base_url

    async def _login(self, email: str, password: str) -> str:
        try:
        
            url = f"{self.AUTH_BASE_URL}/api/fe/v1/login"
            headers = {
                'accept': '*/*',
                'content-type': 'application/json',
                'origin': self.AUTH_BASE_URL,
                'referer': f"{self.AUTH_BASE_URL}/en/login",
                'x-csrf-token': '-.-'
            }
        
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={'email': email, 'password': password},
                    headers=headers
                ) as response:
                    cookies = response.cookies
                    if not cookies:
                        raise Exception('No cookies received in login response')
                    
                    refresh_token = cookies.get('refresh_token')
                    if not refresh_token:
                        raise Exception('No refresh token found in cookies')
                    
                    return refresh_token.value
        except Exception as e:
            raise Exception('Authentication failed during login')

    async def _get_access_token_and_team_id(self, refresh_token: str) -> tuple[str, str]:
        try:
            
            url = f"{self.AUTH_BASE_URL}/api/v1/refresh_token"
            headers = {
                'accept': '*/*',
                'content-type': 'application/json',
                'cookie': f"refresh_token={refresh_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    
                    access_token = data.get('access_token')
                    if not access_token:
                        raise Exception('No access token received from refresh token response')
                    # Extract the active organization ID from the user metadata
                    active_org_id = data.get('user', {}).get('metadata', {}).get('activeOrgId')
                    if not active_org_id:
                        raise Exception('No active organization ID received from refresh token response')
                    return access_token, active_org_id
        except Exception as e:
            raise Exception('Authentication failed when getting access token')

    async def authenticate(self, email: str, password: str) -> tuple[str, str]:
        if not email or not password:
            raise Exception('Authentication credentials not found. Please set AUTH_EMAIL and AUTH_PASSWORD in .env file or environment variables.')
        refresh_token = await self._login(email, password)
        access_token, active_org_id = await self._get_access_token_and_team_id(refresh_token)
        return access_token, active_org_id

