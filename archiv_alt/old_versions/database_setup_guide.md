# 🗄️ Complete Database Setup Guide (Beginner-Friendly)

## What is a Database?
Think of a database like a **giant Excel spreadsheet in the cloud** that:
- Stores your solar radiation data
- Can be accessed from anywhere
- Serves data to your website instantly
- Handles thousands of users simultaneously

## Step 1: Create Supabase Account (5 minutes)

### 1.1 Go to Supabase
- Visit: https://supabase.com
- Click "Start your project" 
- Sign up with GitHub or email

### 1.2 Create New Project
- Click "New Project"
- **Organization:** Choose your account
- **Name:** `solar-calculator-germany`
- **Database Password:** Save this password! You'll need it
- **Region:** Europe (closest to Germany)
- Click "Create new project"
- Wait 2-3 minutes for setup

### 1.3 Get Your Connection Details
After setup, you'll see:
- **Project URL:** `https://abcdefgh.supabase.co`
- **API Key:** `eyJ0eXAiOiJKV1QiLCJhbGciOiJI...` (long string)

**SAVE THESE!** You'll need them later.

## Step 2: Create the Database Table (10 minutes)

### 2.1 Open SQL Editor
- In your Supabase dashboard
- Click "SQL Editor" in the left menu
- Click "New query"

### 2.2 Copy This SQL Code
```sql
-- Create the main table for solar radiation data
CREATE TABLE solar_radiation (
    id BIGSERIAL PRIMARY KEY,
    latitude DECIMAL(6,3) NOT NULL,
    longitude DECIMAL(6,3) NOT NULL,
    tilt INTEGER NOT NULL,
    azimuth INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    poa_direct DECIMAL(8,2) NOT NULL,
    poa_sky_diffuse DECIMAL(8,2) NOT NULL,
    poa_ground_diffuse DECIMAL(8,2) NOT NULL,
    total_radiation DECIMAL(8,2) NOT NULL,
    temperature DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for fast lookups
CREATE INDEX idx_location_config ON solar_radiation 
(latitude, longitude, tilt, azimuth);

CREATE INDEX idx_datetime ON solar_radiation 
(month, day, hour);

-- Add a comment to explain the table
COMMENT ON TABLE solar_radiation IS 'Solar radiation data for Germany from PVGIS';
```

### 2.3 Run the SQL
- Paste the code in the SQL editor
- Click "Run" button
- You should see "Success. No rows returned"

**What this does:**
- Creates a table to store solar data
- Each row = radiation at specific location/time
- Indexes make lookups super fast

## Step 3: Set Up Data Population Scripts

### 3.1 Install Python Dependencies
```bash
pip install supabase python-dotenv
```

### 3.2 Create Environment File
Create `.env` file with your Supabase details:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 3.3 Create Database Manager Script
I'll create this for you...
