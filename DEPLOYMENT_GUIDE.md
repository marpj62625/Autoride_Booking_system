# Admin App Deployment Guide - Option B (Same Project)

## Overview
This guide will help you deploy the admin_app as part of the existing Vercel project.

## Current Configuration

? **vercel.json** - Already configured with routes:
- `/api/*` ? Backend API (Python)
- `/admin/*` ? Admin Website (admin_app)
- `/admin_app/*` ? Admin Website (admin_app)
- `/admin_mobile/*` ? Admin Mobile (admin_mobile/www)
- `/*` ? Frontend (main booking system)

## Deployment Steps

### 1. Commit Your Changes (if using Git)

```cmd
cd c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem
git add vercel.json
git commit -m "Configure admin_app routing for Vercel"
git push
```

### 2. Deploy to Vercel

**Option A: Via Vercel CLI**
```cmd
cd c:\Users\patri\OneDrive\Desktop\AutorideSystem2sides\AutorideSystem
vercel --prod
```

**Option B: Via Vercel Dashboard**
1. Go to https://vercel.com/dashboard
2. Select your `autoride-booking-system` project
3. Click "Deployments" tab
4. Click "Redeploy" button
5. Confirm the deployment

### 3. Add Custom Domain/Subdomain (Optional)

After successful deployment:

1. Go to Project Settings ? Domains
2. Click "Add Existing" button
3. Enter one of these:
   - `admin.autoride-booking-system.vercel.app`
   - `autoride-admin.vercel.app`
4. Click "Add"

### 4. Configure Domain Redirect (Optional)

To make the subdomain point directly to admin:

1. Click "Edit" on the new domain
2. Under "Redirect to Another Domain":
   - Source: `admin.autoride-booking-system.vercel.app`
   - Destination: Leave blank (it will use default routing)
3. Click "Save"

## Access URLs After Deployment

| Service | URL |
|---------|-----|
| Main Booking System | `https://autoride-booking-system.vercel.app` |
| Admin Website | `https://autoride-booking-system.vercel.app/admin/` |
| Admin Mobile | `https://autoride-booking-system.vercel.app/admin_mobile/` |
| API | `https://autoride-booking-system.vercel.app/api/` |
| Admin Subdomain (if configured) | `https://admin.autoride-booking-system.vercel.app` |

## Important Notes

? **Safe Deployment** - All existing endpoints remain unchanged:
- API routes (`/api/*`) continue to work
- Frontend routes continue to work
- Mobile apps will continue to connect to the same API

? **Zero Breaking Changes** - The admin_app has hardcoded API URLs, so it will continue to use the existing API regardless of where it's deployed.

## Verification Steps

After deployment, test these URLs:

1. **API Health Check**
   ```
   https://autoride-booking-system.vercel.app/api/vehicles
   ```

2. **Admin App Access**
   ```
   https://autoride-booking-system.vercel.app/admin/
   ```

3. **Main Frontend**
   ```
   https://autoride-booking-system.vercel.app/
   ```

## Troubleshooting

### Admin page shows 404
- Make sure the `admin_app` folder exists in your repository
- Check that vercel.json is committed and pushed
- Redeploy the project

### API not working
- API routes are unchanged, should work normally
- Check Environment Variables in Vercel dashboard

### Need to rollback?
- Go to Deployments tab in Vercel
- Find the previous working deployment
- Click "..." menu ? "Promote to Production"

## Next Steps

After successful deployment:
1. Test all admin features
2. Test booking system functionality
3. Verify API connections from mobile apps
4. Configure custom domain if needed

---

**Ready to deploy?** Run: `vercel --prod`
