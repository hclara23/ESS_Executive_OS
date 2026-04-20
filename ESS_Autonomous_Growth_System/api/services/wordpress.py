import base64
import httpx
from typing import Optional, Dict, Any
from config import settings

class WordPressClient:
    """WordPress REST API client with JWT authentication."""
    
    def __init__(self):
        self.base_url = settings.WP_URL.rstrip("/")
        self.username = settings.WP_USERNAME
        self.password = settings.WP_PASSWORD
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._auth_mode: Optional[str] = None
    
    async def _get_jwt_token(self) -> str:
        import time
        if self._token and time.time() < self._token_expiry:
            return self._token
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/jwt-auth/v1/token",
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["token"]
            self._token_expiry = time.time() + (6 * 24 * 3600)
            return self._token
    
    async def _headers(self) -> Dict[str, str]:
        if self._auth_mode == "basic":
            return self._basic_headers()

        try:
            token = await self._get_jwt_token()
            self._auth_mode = "jwt"
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        except Exception:
            if not self.username or not self.password:
                raise
            self._auth_mode = "basic"
            return self._basic_headers()

    def _basic_headers(self) -> Dict[str, str]:
        auth = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        return {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        }
    
    async def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        slug: Optional[str] = None,
        meta_description: Optional[str] = None,
        meta_title: Optional[str] = None,
        categories: Optional[list] = None,
        tags: Optional[list] = None,
        featured_media: Optional[int] = None,
        acf_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = await self._headers()
        payload = {
            "title": title,
            "content": content,
            "status": status,
        }
        if slug:
            payload["slug"] = slug
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media:
            payload["featured_media"] = featured_media
        if meta_title or meta_description:
            payload["meta"] = {}
            if meta_title:
                payload["meta"]["_meta_title"] = meta_title
            if meta_description:
                payload["meta"]["_meta_description"] = meta_description
        if acf_fields:
            payload["acf"] = acf_fields
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/posts",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def update_post(self, post_id: int, **kwargs) -> Dict[str, Any]:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}",
                headers=headers,
                json=kwargs,
            )
            response.raise_for_status()
            return response.json()
    
    async def get_post(self, post_id: int) -> Dict[str, Any]:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    
    async def get_posts(self, status: str = "any", per_page: int = 100, page: int = 1) -> list:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/wp-json/wp/v2/posts",
                headers=headers,
                params={"status": status, "per_page": per_page, "page": page},
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_post(self, post_id: int, force: bool = False) -> Dict[str, Any]:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{self.base_url}/wp-json/wp/v2/posts/{post_id}",
                headers=headers,
                params={"force": force},
            )
            response.raise_for_status()
            return response.json()
    
    async def get_pages(self, **kwargs) -> list:
        headers = await self._headers()
        params = {"per_page": 100}
        params.update(kwargs)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/wp-json/wp/v2/pages",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()
    
    async def create_page(self, title: str, content: str, status: str = "draft", slug: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        headers = await self._headers()
        payload = {"title": title, "content": content, "status": status}
        if slug:
            payload["slug"] = slug
        payload.update(kwargs)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/pages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def update_page(self, page_id: int, **kwargs) -> Dict[str, Any]:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/pages/{page_id}",
                headers=headers,
                json=kwargs,
            )
            response.raise_for_status()
            return response.json()
    
    async def upload_media(self, filename: str, content: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
        headers = await self._headers()
        headers["Content-Disposition"] = f"attachment; filename={filename}"
        headers["Content-Type"] = content_type
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/media",
                headers=headers,
                content=content,
            )
            response.raise_for_status()
            return response.json()
    
    async def get_categories(self) -> list:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/wp-json/wp/v2/categories",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    
    async def create_category(self, name: str, description: str = "") -> Dict[str, Any]:
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/wp-json/wp/v2/categories",
                headers=headers,
                json={"name": name, "description": description},
            )
            response.raise_for_status()
            return response.json()
    
    async def test_connection(self) -> bool:
        try:
            await self.get_posts(per_page=1)
            return True
        except Exception:
            return False

wp_client = WordPressClient()
