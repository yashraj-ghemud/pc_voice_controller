"""
Verification tests for WebAgent implementation.

This module contains unit tests that verify the WebAgent correctly implements
the requirements from the spec: web searches, URL opening, response structure,
and error handling.

Validates: Requirements 7.1, 7.2, 7.3, 7.4
"""

import unittest
from unittest.mock import patch, MagicMock
from agents.specialized.web_agent import WebAgent
from agents.models import AgentResponse


class TestWebAgentVerification(unittest.TestCase):
    """Verification tests for WebAgent implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = WebAgent()
    
    def test_agent_initialization(self):
        """Test WebAgent initializes with correct attributes."""
        self.assertEqual(self.agent.name, "WebAgent")
        self.assertEqual(self.agent.agent_type, "web")
        self.assertIn("web searches", self.agent.description.lower())
        self.assertEqual(len(self.agent.ALLOWED_ACTIONS), 2)
        self.assertIn("SEARCH", self.agent.ALLOWED_ACTIONS)
        self.assertIn("OPEN_URL", self.agent.ALLOWED_ACTIONS)
    
    def test_custom_search_engine(self):
        """Test WebAgent can use custom search engine."""
        custom_engine = "https://duckduckgo.com/?q={query}"
        agent = WebAgent(search_engine=custom_engine)
        self.assertEqual(agent.search_engine, custom_engine)
    
    @patch('webbrowser.open')
    def test_search_success(self, mock_open):
        """Test successful web search execution."""
        # Requirement 7.1: Perform web search and open results
        mock_open.return_value = True
        
        response = self.agent.search("Python programming")
        
        # Verify AgentResponse structure (Requirement 7.4)
        self.assertIsInstance(response, AgentResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.agent_name, "WebAgent")
        self.assertEqual(response.action_taken, "SEARCH")
        
        # Verify result contains query and URL
        self.assertIn("query", response.result)
        self.assertEqual(response.result["query"], "Python programming")
        self.assertIn("search_url", response.result)
        self.assertIn("browser_opened", response.result)
        self.assertTrue(response.result["browser_opened"])
        
        # Verify browser was opened with correct URL
        mock_open.assert_called_once()
        called_url = mock_open.call_args[0][0]
        self.assertIn("Python+programming", called_url)
        self.assertTrue(called_url.startswith("http"))
    
    @patch('webbrowser.open')
    def test_search_empty_query(self, mock_open):
        """Test search with empty query returns error."""
        response = self.agent.search("")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertIn("cannot be empty", response.error.lower())
        self.assertFalse(response.retry_recommended)
        
        # Browser should not be called
        mock_open.assert_not_called()
    
    @patch('webbrowser.open')
    def test_search_whitespace_query(self, mock_open):
        """Test search with whitespace-only query returns error."""
        response = self.agent.search("   ")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        mock_open.assert_not_called()
    
    @patch('webbrowser.open')
    def test_search_browser_failure(self, mock_open):
        """Test search when browser fails to open."""
        mock_open.return_value = False
        
        response = self.agent.search("test query")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertTrue(response.retry_recommended)
    
    @patch('webbrowser.open')
    def test_search_exception_handling(self, mock_open):
        """Test search handles exceptions gracefully."""
        mock_open.side_effect = Exception("Browser error")
        
        response = self.agent.search("test query")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertIn("Browser error", response.error)
        self.assertTrue(response.retry_recommended)
    
    @patch('webbrowser.open')
    def test_open_url_success(self, mock_open):
        """Test successful URL opening."""
        # Requirement 7.2: Open URL in default browser
        mock_open.return_value = True
        
        response = self.agent.open_url("https://www.python.org")
        
        # Verify AgentResponse structure (Requirement 7.4)
        self.assertIsInstance(response, AgentResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.agent_name, "WebAgent")
        self.assertEqual(response.action_taken, "OPEN_URL")
        
        # Verify result contains URL
        self.assertIn("url", response.result)
        self.assertEqual(response.result["url"], "https://www.python.org")
        self.assertIn("browser_opened", response.result)
        self.assertTrue(response.result["browser_opened"])
        
        # Verify browser was opened with correct URL
        mock_open.assert_called_once_with("https://www.python.org")
    
    @patch('webbrowser.open')
    def test_open_url_without_protocol(self, mock_open):
        """Test URL opening adds http:// prefix when missing."""
        mock_open.return_value = True
        
        response = self.agent.open_url("python.org")
        
        self.assertTrue(response.success)
        self.assertEqual(response.result["url"], "http://python.org")
        mock_open.assert_called_once_with("http://python.org")
    
    @patch('webbrowser.open')
    def test_open_url_with_https(self, mock_open):
        """Test URL opening preserves https protocol."""
        mock_open.return_value = True
        
        response = self.agent.open_url("https://secure.example.com")
        
        self.assertTrue(response.success)
        self.assertEqual(response.result["url"], "https://secure.example.com")
        mock_open.assert_called_once_with("https://secure.example.com")
    
    @patch('webbrowser.open')
    def test_open_url_empty(self, mock_open):
        """Test open_url with empty URL returns error."""
        response = self.agent.open_url("")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertIn("cannot be empty", response.error.lower())
        self.assertFalse(response.retry_recommended)
        
        # Browser should not be called
        mock_open.assert_not_called()
    
    @patch('webbrowser.open')
    def test_open_url_whitespace(self, mock_open):
        """Test open_url with whitespace-only URL returns error."""
        response = self.agent.open_url("   ")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        mock_open.assert_not_called()
    
    @patch('webbrowser.open')
    def test_open_url_browser_failure(self, mock_open):
        """Test open_url when browser fails to open."""
        mock_open.return_value = False
        
        response = self.agent.open_url("https://example.com")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertTrue(response.retry_recommended)
    
    @patch('webbrowser.open')
    def test_open_url_exception_handling(self, mock_open):
        """Test open_url handles exceptions gracefully."""
        mock_open.side_effect = Exception("Network error")
        
        response = self.agent.open_url("https://example.com")
        
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertIn("Network error", response.error)
        self.assertTrue(response.retry_recommended)
    
    @patch('webbrowser.open')
    def test_execute_task_search(self, mock_open):
        """Test execute_task routes SEARCH action correctly."""
        mock_open.return_value = True
        
        result = self.agent.execute_task("SEARCH", {
            "action": "SEARCH",
            "params": {"query": "test search"}
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["action_taken"], "SEARCH")
        mock_open.assert_called_once()
    
    @patch('webbrowser.open')
    def test_execute_task_open_url(self, mock_open):
        """Test execute_task routes OPEN_URL action correctly."""
        mock_open.return_value = True
        
        result = self.agent.execute_task("OPEN_URL", {
            "action": "OPEN_URL",
            "params": {"url": "https://example.com"}
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["action_taken"], "OPEN_URL")
        mock_open.assert_called_once_with("https://example.com")
    
    def test_execute_task_unknown_action(self):
        """Test execute_task handles unknown action."""
        result = self.agent.execute_task("UNKNOWN_ACTION", {
            "action": "UNKNOWN_ACTION",
            "params": {}
        })
        
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])
        self.assertIn("unknown", result["error"].lower())
    
    @patch('webbrowser.open')
    def test_execute_task_with_alternative_param_names(self, mock_open):
        """Test execute_task handles alternative parameter names."""
        mock_open.return_value = True
        
        # Test search with alternative param name
        result = self.agent.execute_task("SEARCH", {
            "action": "SEARCH",
            "params": {"search_query": "alternative param"}
        })
        self.assertTrue(result["success"])
        
        # Test open_url with alternative param name
        result = self.agent.execute_task("OPEN_URL", {
            "action": "OPEN_URL",
            "params": {"link": "https://example.com"}
        })
        self.assertTrue(result["success"])
    
    def test_agent_response_validation(self):
        """Test that agent responses pass validation."""
        with patch('webbrowser.open', return_value=True):
            response = self.agent.search("test")
            response.validate()  # Should not raise
            
            response = self.agent.open_url("https://example.com")
            response.validate()  # Should not raise
    
    def test_repr(self):
        """Test string representation of WebAgent."""
        repr_str = repr(self.agent)
        self.assertIn("WebAgent", repr_str)
        self.assertIn("name='WebAgent'", repr_str)
        self.assertIn("allowed_actions=2", repr_str)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
