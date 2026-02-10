@echo off
echo Testing API Videos Endpoints
echo ============================

set BASE_URL=http://127.0.0.1:8000

echo.
echo 1. Testing GET /api/videos (list videos)...
curl -X GET "%BASE_URL%/api/videos" -H "Content-Type: application/json" -v
echo.

echo.
echo 2. Testing GET /api/videos/categories (list categories)...
curl -X GET "%BASE_URL%/api/videos/categories" -H "Content-Type: application/json" -v
echo.

echo.
echo 3. Testing POST /api/videos/debug-add-samples (add sample videos)...
curl -X POST "%BASE_URL%/api/videos/debug-add-samples" -H "Content-Type: application/json" -v
echo.

echo.
echo 4. Testing POST /api/videos/refresh (refresh videos)...
curl -X POST "%BASE_URL%/api/videos/refresh" -H "Content-Type: application/json" -v
echo.

echo.
echo 5. Testing GET /api/videos/1 (get specific video - may fail if no videos exist)...
curl -X GET "%BASE_URL%/api/videos/1" -H "Content-Type: application/json" -v
echo.

echo.
echo Testing OAuth Authentication Endpoints
echo =====================================

echo.
echo 6. Testing GET /oauth/youtube/authorize (start OAuth flow)...
curl -X GET "%BASE_URL%/oauth/youtube/authorize" -H "Content-Type: application/json" -v
echo.

echo.
echo 7. Testing GET /oauth/facebook/authorize (start OAuth flow)...
curl -X GET "%BASE_URL%/oauth/facebook/authorize" -H "Content-Type: application/json" -v
echo.

echo.
echo 8. Testing GET /oauth/connections (list OAuth connections)...
curl -X GET "%BASE_URL%/oauth/connections" -H "Content-Type: application/json" -v
echo.

echo.
echo ============================
echo API Testing Complete
echo ============================
pause
