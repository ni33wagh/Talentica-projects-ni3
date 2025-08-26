import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.jenkins import JenkinsClient
from app.config import settings


class TestJenkinsClient:
    """Test Jenkins client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = JenkinsClient()
        self.client.base_url = "https://jenkins.example.com"
        self.client.username = "testuser"
        self.client.api_token = "testtoken"
    
    def test_build_url(self):
        """Test URL building functionality."""
        # Test basic URL building
        url = self.client._build_url("/api/json")
        assert url == "https://jenkins.example.com/api/json"
        
        # Test with trailing slash in base URL
        self.client.base_url = "https://jenkins.example.com/"
        url = self.client._build_url("/api/json")
        assert url == "https://jenkins.example.com/api/json"
        
        # Test with no base URL
        self.client.base_url = None
        with pytest.raises(ValueError, match="Jenkins URL not configured"):
            self.client._build_url("/api/json")
    
    def test_get_auth(self):
        """Test authentication tuple generation."""
        auth = self.client._get_auth()
        assert auth == ("testuser", "testtoken")
        
        # Test with missing credentials
        self.client.username = None
        auth = self.client._get_auth()
        assert auth is None
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key = self.client._get_cache_key("GET", "/api/json")
        assert key == "GET|https://jenkins.example.com/api/json"
        
        # Test with parameters
        params = {"tree": "jobs[name]"}
        key = self.client._get_cache_key("GET", "/api/json", params)
        assert "GET|https://jenkins.example.com/api/json|" in key
        assert "jobs[name]" in key
    
    def test_cache_operations(self):
        """Test cache get/set operations."""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Test cache miss
        result = self.client._get_cached_response(cache_key)
        assert result is None
        
        # Test cache set and get
        self.client._set_cached_response(cache_key, test_data)
        result = self.client._get_cached_response(cache_key)
        assert result == test_data
    
    @pytest.mark.asyncio
    async def test_get_crumb_success(self):
        """Test successful crumb retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "crumbRequestField": "Jenkins-Crumb",
            "crumb": "test-crumb-value"
        }
        mock_response.raise_for_status.return_value = None
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.client.get_crumb()
            
            assert result == {"Jenkins-Crumb": "test-crumb-value"}
            assert self.client._crumb == {"Jenkins-Crumb": "test-crumb-value"}
    
    @pytest.mark.asyncio
    async def test_get_crumb_failure(self):
        """Test crumb retrieval failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")
            
            result = await self.client.get_crumb()
            
            assert result is None
    
    def test_get_headers_with_crumb(self):
        """Test header generation with crumb."""
        self.client._crumb = {"Jenkins-Crumb": "test-crumb"}
        self.client._crumb_expiry = 9999999999  # Far future
        
        headers = self.client._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Jenkins-Crumb"] == "test-crumb"
    
    def test_get_headers_without_crumb(self):
        """Test header generation without crumb."""
        headers = self.client._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert "Jenkins-Crumb" not in headers
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add some test data to cache
        self.client._cache["test_key"] = ("test_data", 1234567890)
        
        self.client.clear_cache()
        
        assert len(self.client._cache) == 0


class TestJenkinsClientIntegration:
    """Integration tests for Jenkins client."""
    
    @pytest.mark.asyncio
    async def test_list_jobs_mock(self):
        """Test list_jobs with mocked response."""
        client = JenkinsClient()
        client.base_url = "https://jenkins.example.com"
        client.username = "testuser"
        client.api_token = "testtoken"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jobs": [
                {"name": "test-job-1", "url": "http://jenkins/job/test-job-1"},
                {"name": "test-job-2", "url": "http://jenkins/job/test-job-2"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            jobs = await client.list_jobs()
            
            assert len(jobs) == 2
            assert jobs[0]["name"] == "test-job-1"
            assert jobs[1]["name"] == "test-job-2"
    
    @pytest.mark.asyncio
    async def test_list_builds_mock(self):
        """Test list_builds with mocked response."""
        client = JenkinsClient()
        client.base_url = "https://jenkins.example.com"
        client.username = "testuser"
        client.api_token = "testtoken"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "builds": [
                {"number": 1, "result": "SUCCESS"},
                {"number": 2, "result": "FAILURE"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            builds = await client.list_builds("test-job", limit=10)
            
            assert len(builds) == 2
            assert builds[0]["number"] == 1
            assert builds[1]["number"] == 2
    
    @pytest.mark.asyncio
    async def test_get_build_mock(self):
        """Test get_build with mocked response."""
        client = JenkinsClient()
        client.base_url = "https://jenkins.example.com"
        client.username = "testuser"
        client.api_token = "testtoken"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 1,
            "result": "SUCCESS",
            "duration": 120000,
            "timestamp": 1640995200000
        }
        mock_response.raise_for_status.return_value = None
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            build = await client.get_build("test-job", 1)
            
            assert build["number"] == 1
            assert build["result"] == "SUCCESS"
            assert build["duration"] == 120000


class TestJenkinsClientErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_403_retry_with_crumb(self):
        """Test 403 error handling with crumb retry."""
        client = JenkinsClient()
        client.base_url = "https://jenkins.example.com"
        client.username = "testuser"
        client.api_token = "testtoken"
        
        # Mock first response (403)
        mock_403_response = MagicMock()
        mock_403_response.status_code = 403
        mock_403_response.raise_for_status.side_effect = Exception("403")
        
        # Mock second response (success after crumb refresh)
        mock_success_response = MagicMock()
        mock_success_response.json.return_value = {"jobs": []}
        mock_success_response.raise_for_status.return_value = None
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.request.side_effect = [mock_403_response, mock_success_response]
            
            # Mock crumb retrieval
            with patch.object(client, 'get_crumb', return_value={"Jenkins-Crumb": "new-crumb"}):
                jobs = await client.list_jobs()
                
                assert jobs == []
                # Verify request was made twice (original + retry)
                assert mock_instance.request.call_count == 2
