#!/usr/bin/env python3
"""
Comprehensive API Test Script for Quiz Generator
Tests all endpoints and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_LECTURE_DATA = {
    "courseCode": "TEST101",
    "year": 2027,
    "quarter": "Test",
    "videoId": "test_video_001",
    "videoUrl": "https://example.com/test_video.mp4",
    "transcriptUrl": "http://localhost:8080/test_transcript.txt"
}

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.lecture_id = None
        self.quiz_id = None
        
    def print_test_header(self, test_name: str):
        """Print a formatted test header"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {test_name}")
        print(f"{'='*60}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Dict:
        """Make HTTP request and handle response"""
        url = f"{self.api_base}{endpoint}" if endpoint.startswith('/') else f"{self.api_base}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url)
            elif method.upper() == "POST":
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                return response.json() if response.content else {}
            else:
                self.print_error(f"Expected status {expected_status}, got {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return {}
                
        except requests.exceptions.ConnectionError:
            self.print_error(f"Could not connect to {url}")
            self.print_error("Make sure the API server is running on the correct port")
            return {}
        except Exception as e:
            self.print_error(f"Request failed: {str(e)}")
            return {}
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        self.print_test_header("Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Health check passed: {data}")
                return True
            else:
                self.print_error(f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health check failed: {str(e)}")
            return False
    
    def test_create_lecture(self) -> bool:
        """Test lecture creation"""
        self.print_test_header("Create Lecture")
        
        result = self.make_request("POST", "/lectures", TEST_LECTURE_DATA, 201)
        
        if result and "id" in result:
            self.lecture_id = result["id"]
            self.print_success(f"Lecture created with ID: {self.lecture_id}")
            return True
        else:
            self.print_error("Failed to create lecture")
            return False
    
    def test_get_lecture(self) -> bool:
        """Test getting lecture information"""
        if not self.lecture_id:
            self.print_error("No lecture ID available for testing")
            return False
            
        self.print_test_header("Get Lecture")
        
        result = self.make_request("GET", f"/lectures/{self.lecture_id}")
        
        if result and "_id" in result:
            self.print_success(f"Retrieved lecture: {result.get('courseCode')} - {result.get('videoId')}")
            self.print_info(f"Status: {result.get('status')}")
            return True
        else:
            self.print_error("Failed to retrieve lecture")
            return False
    
    def test_process_lecture(self) -> bool:
        """Test lecture processing"""
        if not self.lecture_id:
            self.print_error("No lecture ID available for testing")
            return False
            
        self.print_test_header("Process Lecture")
        
        result = self.make_request("POST", f"/lectures/{self.lecture_id}/process")
        
        if result and "message" in result:
            self.print_success(f"Processing started: {result['message']}")
            return True
        else:
            self.print_error("Failed to start processing")
            return False
    
    def test_get_lecture_status(self) -> bool:
        """Test getting lecture status"""
        if not self.lecture_id:
            self.print_error("No lecture ID available for testing")
            return False
            
        self.print_test_header("Get Lecture Status")
        
        result = self.make_request("GET", f"/lectures/{self.lecture_id}/status")
        
        if result and "status" in result:
            status = result["status"]
            self.print_success(f"Lecture status: {status}")
            
            if status == "completed":
                self.print_success("Lecture processing completed!")
                return True
            elif status == "failed":
                self.print_error("Lecture processing failed")
                return False
            else:
                self.print_info(f"Lecture is still {status}")
                return True
        else:
            self.print_error("Failed to get lecture status")
            return False
    
    def test_get_quiz(self) -> bool:
        """Test getting quiz data"""
        if not self.lecture_id:
            self.print_error("No lecture ID available for testing")
            return False
            
        self.print_test_header("Get Quiz")
        
        result = self.make_request("GET", f"/lectures/{self.lecture_id}/quiz")
        
        if result and "lectureId" in result:
            self.quiz_id = result.get("_id")
            self.print_success(f"Quiz retrieved successfully")
            self.print_info(f"Quiz ID: {self.quiz_id}")
            self.print_info(f"Format: {result.get('format')}")
            self.print_info(f"File URL: {result.get('fileUrl')}")
            return True
        else:
            self.print_error("Failed to retrieve quiz")
            return False
    
    def test_get_quiz_url(self) -> bool:
        """Test getting quiz URL"""
        if not self.lecture_id:
            self.print_error("No lecture ID available for testing")
            return False
            
        self.print_test_header("Get Quiz URL")
        
        result = self.make_request("GET", f"/lectures/{self.lecture_id}/quiz/url")
        
        if result and "fileUrl" in result:
            self.print_success(f"Quiz URL retrieved: {result['fileUrl']}")
            return True
        else:
            self.print_error("Failed to retrieve quiz URL")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid data"""
        self.print_test_header("Error Handling Tests")
        
        # Test 1: Invalid lecture ID
        self.print_info("Testing with invalid lecture ID...")
        result = self.make_request("GET", "/lectures/invalid_id", expected_status=400)
        if not result:
            self.print_success("Correctly handled invalid lecture ID")
        
        # Test 2: Invalid lecture data
        self.print_info("Testing with invalid lecture data...")
        invalid_data = {"courseCode": "TEST"}  # Missing required fields
        result = self.make_request("POST", "/lectures", invalid_data, expected_status=422)
        if not result:
            self.print_success("Correctly handled invalid lecture data")
        
        return True
    
    def wait_for_processing(self, max_wait_time: int = 300) -> bool:
        """Wait for lecture processing to complete"""
        self.print_test_header("Waiting for Processing")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            result = self.make_request("GET", f"/lectures/{self.lecture_id}/status")
            
            if result and "status" in result:
                status = result["status"]
                self.print_info(f"Current status: {status}")
                
                if status == "completed":
                    self.print_success("Processing completed!")
                    return True
                elif status == "failed":
                    self.print_error("Processing failed")
                    return False
                else:
                    self.print_info(f"Still processing... ({status})")
                    time.sleep(10)  # Wait 10 seconds before checking again
            else:
                self.print_error("Failed to get status")
                return False
        
        self.print_error(f"Processing timed out after {max_wait_time} seconds")
        return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting Comprehensive API Tests")
        print(f"📍 Testing API at: {self.base_url}")
        
        results = {}
        
        # Test 1: Health Check
        results["health_check"] = self.test_health_check()
        if not results["health_check"]:
            self.print_error("Health check failed. Stopping tests.")
            return results
        
        # Test 2: Create Lecture
        results["create_lecture"] = self.test_create_lecture()
        if not results["create_lecture"]:
            self.print_error("Lecture creation failed. Stopping tests.")
            return results
        
        # Test 3: Get Lecture
        results["get_lecture"] = self.test_get_lecture()
        
        # Test 4: Process Lecture
        results["process_lecture"] = self.test_process_lecture()
        if not results["process_lecture"]:
            self.print_error("Lecture processing failed. Stopping tests.")
            return results
        
        # Test 5: Wait for Processing
        results["wait_for_processing"] = self.wait_for_processing()
        
        # Test 6: Get Status
        results["get_status"] = self.test_get_lecture_status()
        
        # Test 7: Get Quiz (only if processing completed)
        if results["wait_for_processing"]:
            results["get_quiz"] = self.test_get_quiz()
            results["get_quiz_url"] = self.test_get_quiz_url()
        
        # Test 8: Error Handling
        results["error_handling"] = self.test_error_handling()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        self.print_test_header("Test Summary")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Your API is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the logs above for details.")

def main():
    """Main function to run the tests"""
    # Check if API server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API server is not responding correctly at {BASE_URL}")
            print("Make sure the server is running with: uvicorn api.main:app --reload --port 3000 --host 0.0.0.0")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to API server at {BASE_URL}")
        print("Make sure the server is running with: uvicorn api.main:app --reload --port 3000 --host 0.0.0.0")
        sys.exit(1)
    
    # Run tests
    tester = APITester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 