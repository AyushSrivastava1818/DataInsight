@echo off
curl -v -X OPTIONS -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" http://localhost:8000/api/datasets/upload
