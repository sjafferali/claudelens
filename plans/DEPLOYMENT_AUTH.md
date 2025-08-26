# Authentication Setup for Remote Deployment

## Quick Start

For your deployment at `http://c-rat.local.samir.systems:21855`, you need to initialize the API key in the database.

### Step 1: Initialize the API Key

**Option A: Run directly on your server (Recommended)**

SSH into your server and run:

```bash
# Clone or copy the init script to your server
docker exec -it <mongodb-container-name> mongosh claudelens --eval '
db.users.updateOne(
  { username: "admin" },
  {
    $set: {
      email: "admin@claudelens.local",
      username: "admin",
      role: "admin",
      permissions: ["*"],
      api_keys: [{
        name: "Default API Key",
        key_hash: "1913026954bf7c5c5098a2e2ac5f2f98e5bb951c26ca8f88ce9e7f88e2c96378",
        created_at: new Date(),
        expires_at: new Date(Date.now() + 365*24*60*60*1000),
        last_used: null,
        active: true
      }],
      created_at: new Date(),
      updated_at: new Date(),
      is_active: true,
      storage_used: 0,
      storage_limit: null,
      rate_limits: {
        requests_per_minute: 1000,
        requests_per_hour: 10000
      }
    }
  },
  { upsert: true }
)
'
```

**Option B: Use the Python script**

Copy the `backend/scripts/init_api_key_simple.py` script to your server and run:

```bash
python init_api_key_simple.py
```

The script has the API key and MongoDB URI hardcoded for convenience.

### Step 2: Access the Application

1. Open your browser and go to: `http://c-rat.local.samir.systems:21855`
2. You will be redirected to the login page
3. Enter your API key: `ohc3EeG9Ibai5uerieg2ahp7oheeYaec`
4. Click "Sign In"

### Alternative: Use Environment Variable (No Login Required)

If you prefer to skip the login page, you can set the API key as an environment variable when building:

1. Create `.env` file in the frontend directory:
```bash
echo "VITE_API_KEY=ohc3EeG9Ibai5uerieg2ahp7oheeYaec" > frontend/.env
```

2. Build the frontend:
```bash
cd frontend
npm run build
```

3. Build the Docker image:
```bash
docker build -t claudelens:latest .
```

4. Deploy the new image to your server

With this approach, the app will use the API key automatically and won't show a login page.

### Step 3: Rebuild and Deploy (With Login Page)

If you want to use the login page:

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Build the Docker image:
```bash
docker build -t claudelens:latest .
```

3. Deploy the new image to your server

## Authentication Flow

The authentication system works as follows:

1. **Frontend**:
   - Login page at `/login` accepts API key
   - Stores API key in browser localStorage
   - Sends API key in `X-API-Key` header with all requests
   - Protected routes redirect to login if no API key

2. **Backend**:
   - Requires `X-API-Key` header for all API requests from remote IPs
   - Validates API key against hashed keys in database
   - Associates requests with user tenant for data isolation
   - Admin users can access all data

## Troubleshooting

### "Authentication required" error
- Make sure you've run the init_api_key.py script
- Verify the API key is correct
- Check that MongoDB is accessible

### Cannot access after login
- Clear browser cache and localStorage
- Try logging out and logging in again
- Check browser console for errors

### API key not working
- Ensure the API key was properly initialized in the database
- Check MongoDB logs for connection issues
- Verify the MongoDB URI is correct

## Security Notes

- API keys are hashed using SHA256 before storage
- Each user's data is isolated by tenant ID
- Admin users have access to all data
- API keys can be revoked by setting `active: false` in database
