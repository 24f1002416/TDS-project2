"""
Test script to verify your endpoint is working correctly
"""

import requests
import json
import sys


def test_health(base_url):
    """Test health endpoint"""
    print(f"\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✓ Health check passed: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {str(e)}")
        return False


def test_invalid_json(base_url):
    """Test with invalid JSON"""
    print(f"\n2. Testing invalid JSON handling...")
    try:
        response = requests.post(
            f"{base_url}/quiz",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 400:
            print(f"✓ Invalid JSON correctly rejected (400)")
            return True
        else:
            print(f"✗ Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {str(e)}")
        return False


def test_invalid_secret(base_url, email):
    """Test with invalid secret"""
    print(f"\n3. Testing invalid secret handling...")
    try:
        payload = {
            "email": email,
            "secret": "wrong-secret",
            "url": "https://example.com/test"
        }
        response = requests.post(
            f"{base_url}/quiz",
            json=payload,
            timeout=10
        )
        if response.status_code == 403:
            print(f"✓ Invalid secret correctly rejected (403)")
            return True
        else:
            print(f"✗ Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {str(e)}")
        return False


def test_demo_quiz(base_url, email, secret):
    """Test with demo quiz"""
    print(f"\n4. Testing demo quiz (this may take a minute)...")
    try:
        payload = {
            "email": email,
            "secret": secret,
            "url": "https://tds-llm-analysis.s-anand.net/demo"
        }
        response = requests.post(
            f"{base_url}/quiz",
            json=payload,
            timeout=180  # 3 minutes
        )

        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print(f"✓ Demo quiz accepted")
            return True
        else:
            print(f"✗ Demo quiz failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Test error: {str(e)}")
        return False


def main():
    """Main test runner"""
    print("=" * 60)
    print("TDS Project 2 - Endpoint Testing Script")
    print("=" * 60)

    # Get configuration
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = input("Enter your endpoint URL (e.g., http://localhost:5000): ").strip()

    if len(sys.argv) > 2:
        email = sys.argv[2]
    else:
        email = input("Enter your email: ").strip()

    if len(sys.argv) > 3:
        secret = sys.argv[3]
    else:
        secret = input("Enter your secret: ").strip()

    # Remove trailing slash from URL
    base_url = base_url.rstrip('/')

    print(f"\nTesting endpoint: {base_url}")
    print(f"Email: {email}")
    print(f"Secret: {'*' * len(secret)}")

    # Run tests
    results = []
    results.append(("Health Check", test_health(base_url)))
    results.append(("Invalid JSON", test_invalid_json(base_url)))
    results.append(("Invalid Secret", test_invalid_secret(base_url, email)))
    results.append(("Demo Quiz", test_demo_quiz(base_url, email, secret)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your endpoint is ready for submission.")
    else:
        print("\n⚠ Some tests failed. Please fix the issues before submitting.")

    print("=" * 60)


if __name__ == "__main__":
    main()
