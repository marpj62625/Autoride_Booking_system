# Vercel Redeployment Guide - Fix Past Bookings 404

## Problem
The Past Bookings tab shows a 404 error because Vercel hasn't redeployed with the new `/api/bookings/past` endpoint.

## Solution: Trigger Vercel Redeployment

### Option 1: Automatic Redeployment (Recommended)

Vercel should automatically redeploy when you push to Git. Since you already pushed, check:

1. **Go to Vercel Dashboard:**
   - Visit: https://vercel.com/dashboard
   - Find your project: `Autoride_Booking_system`

2. **Check Deployment Status:**
   - Look for the latest deployment
   - Status should be "Ready" or "Building"
   - If it says "Failed", click on it to see error logs

3. **Wait for Deployment:**
   - Deployments usually take 2-5 minutes
   - Once status is "Ready", test the app again

### Option 2: Manual Redeploy

If automatic deployment didn't trigger:

1. **Go to Vercel Dashboard:**
   - https://vercel.com/dashboard
   - Select your project

2. **Go to Deployments Tab:**
   - Click on the latest deployment
   - Click the "..." menu (three dots)
   - Select "Redeploy"
   - Confirm the redeployment

3. **Wait for Completion:**
   - Monitor the build logs
   - Wait for "Ready" status

### Option 3: Force Push (If needed)

If Vercel isn't picking up changes:

```bash
# Make a small change to trigger deployment
echo "# Trigger deployment" >> README.md

# Commit and push
git add README.md
git commit -m "chore: trigger Vercel redeployment"
git push origin main
```

## Verification Steps

After redeployment completes:

1. **Check Vercel Logs:**
   - Go to your deployment in Vercel
   - Click "Functions" tab
   - Look for `/api/bookings/past` in the function list

2. **Test the Endpoint:**
   - Open: `https://your-app.vercel.app/api/bookings/past?page=1&page_size=10`
   - Should return JSON with bookings data
   - Should NOT return 404

3. **Test in Mobile App:**
   - Open admin mobile app
   - Click "Past Bookings" tab
   - Should load bookings successfully

## Common Issues

### Issue 1: Build Fails

**Symptoms:** Deployment status shows "Failed"

**Solution:**
1. Click on the failed deployment
2. Read the build logs
3. Common causes:
   - Missing dependencies in `requirements.txt`
   - Python syntax errors
   - Import errors

**Fix:**
```bash
# Check if all dependencies are listed
cat requirements.txt

# Add missing dependencies
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "fix: update dependencies"
git push origin main
```

### Issue 2: Route Not Found After Deployment

**Symptoms:** Deployment succeeds but endpoint still returns 404

**Possible Causes:**
1. Blueprint not registered in `backend/app.py`
2. Route path mismatch
3. Vercel caching old version

**Solution:**

**Check Blueprint Registration:**
```python
# In backend/app.py, verify these lines exist:
from routers.booking_routes import booking_bp
app.register_blueprint(booking_bp)
```

**Clear Vercel Cache:**
1. Go to Vercel Dashboard
2. Project Settings ? General
3. Scroll to "Build & Development Settings"
4. Click "Clear Cache"
5. Redeploy

### Issue 3: Environment Variables

**Symptoms:** Endpoint works locally but not on Vercel

**Solution:**
1. Go to Vercel Dashboard
2. Project Settings ? Environment Variables
3. Verify all required variables are set:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - Any other required variables

## Debug: Check Vercel Function Logs

1. **Go to Vercel Dashboard**
2. **Select your project**
3. **Click "Functions" tab**
4. **Find `/api/bookings/past`**
   - If it's listed: Endpoint is deployed ?
   - If it's NOT listed: Deployment issue ?

5. **Click on the function**
6. **View logs** to see any errors

## Test Endpoint Directly

Once deployed, test the endpoint directly in your browser:

```
https://your-vercel-app.vercel.app/api/bookings/past?page=1&page_size=10
```

**Expected Response:**
```json
{
  "bookings": [...],
  "page": 1,
  "page_size": 10,
  "total": 50,
  "total_pages": 5
}
```

**If you get 404:**
- Endpoint not deployed yet
- Check deployment status
- Check function logs

## Vercel Configuration Check

Verify `vercel.json` has correct configuration:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "api/index.py"
    }
  ]
}
```

And `api/index.py` imports the Flask app:

```python
from app import app
```

## Quick Checklist

- [ ] Code pushed to Git (main branch)
- [ ] Vercel deployment triggered
- [ ] Deployment status is "Ready"
- [ ] Function `/api/bookings/past` appears in Vercel Functions tab
- [ ] Endpoint returns 200 when tested directly
- [ ] Past Bookings tab loads in mobile app

## Still Not Working?

If the issue persists after redeployment:

1. **Check Vercel Deployment Logs:**
   - Look for Python errors
   - Look for import errors
   - Look for database connection errors

2. **Verify File Structure:**
   ```
   AutorideSystem/
   ??? api/
   ?   ??? index.py (imports from backend/app.py)
   ??? backend/
   ?   ??? app.py (registers booking_bp)
   ?   ??? routers/
   ?       ??? booking_routes.py (has /api/bookings/past route)
   ??? vercel.json
   ```

3. **Check Git Commit:**
   ```bash
   # Verify the files were committed
   git log --oneline -1
   git show HEAD --name-only
   ```

4. **Contact Vercel Support:**
   - Provide deployment URL
   - Provide error logs
   - Describe the issue

---

## Summary

**The fix is simple:**
1. ? Code is already pushed to Git
2. ? Wait for Vercel to redeploy (2-5 minutes)
3. ? Test the endpoint
4. ? Verify in mobile app

**If Vercel hasn't redeployed automatically, manually trigger a redeployment from the Vercel Dashboard.**

---

**Last Updated:** January 2025  
**Status:** Ready to Deploy
