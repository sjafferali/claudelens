#!/bin/bash

# Test script to verify nginx redirect behavior

echo "Testing nginx redirect behavior..."
echo "================================"

# Test with trailing slash
echo -e "\n1. Testing with trailing slash:"
echo "Request: http://localhost:21855/api/v1/projects/"
curl -v -L http://localhost:21855/api/v1/projects/ 2>&1 | grep -E "< HTTP|< Location:|^>"

# Test without trailing slash
echo -e "\n2. Testing without trailing slash:"
echo "Request: http://localhost:21855/api/v1/projects"
curl -v -L http://localhost:21855/api/v1/projects 2>&1 | grep -E "< HTTP|< Location:|^>"

# Test health endpoint
echo -e "\n3. Testing health endpoint:"
echo "Request: http://localhost:21855/health"
curl -v http://localhost:21855/health 2>&1 | grep -E "< HTTP|< Location:|^>"

echo -e "\n================================"
echo "If redirects are fixed, you should see:"
echo "- No Location headers"
echo "- Direct HTTP/1.1 200 OK responses"
echo "- No protocol changes (http to https)"
echo "- Port 21855 preserved in all requests"
