# Scheduler Executor Deployment Guide

## Overview

The scheduler executor runs scheduled payments, recurring transfers, and conditional tasks. It operates independently from the main Streamlit app.

## Deployment Options

### Option 1: Railway (Recommended for MVP)

1. **Create a new service in Railway:**
   ```bash
   # In your Railway project, add a new service from the same repo
   # Set the start command:
   python scheduler_executor.py --mode worker --interval 60
   ```

2. **Set environment variables:**
   ```
   SUPABASE_URL=your-supabase-url
   SUPABASE_SERVICE_KEY=your-service-key
   SCHEDULER_ENCRYPTION_SECRET=a-random-32-byte-secret
   ```

3. **Deploy**

### Option 2: Fly.io

1. **Create `fly.toml`:**
   ```toml
   app = "usdchat-scheduler"
   primary_region = "iad"

   [build]
     builder = "paketobuildpacks/builder:base"

   [env]
     PYTHONUNBUFFERED = "1"

   [processes]
     worker = "python scheduler_executor.py --mode worker --interval 60"

   [[services]]
     internal_port = 8080
     protocol = "tcp"

     [[services.ports]]
       port = 80
   ```

2. **Deploy:**
   ```bash
   fly launch
   fly secrets set SUPABASE_URL=... SUPABASE_SERVICE_KEY=... SCHEDULER_ENCRYPTION_SECRET=...
   fly deploy
   ```

### Option 3: External Cron (Simplest)

Use a cron service like [cron-job.org](https://cron-job.org), [EasyCron](https://www.easycron.com), or GitHub Actions to call the executor.

1. **Deploy HTTP endpoint:**
   ```bash
   python scheduler_executor.py --mode http --port 8080
   ```

2. **Set up cron job:**
   ```
   URL: https://your-domain.com/execute
   Method: POST
   Headers: Authorization: Bearer YOUR_TASK_EXECUTOR_SECRET
   Frequency: Every minute
   ```

### Option 4: Supabase Edge Function

Create `supabase/functions/execute-tasks/index.ts`:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Get due tasks
  const now = new Date().toISOString()
  const { data: tasks, error } = await supabase
    .from('scheduled_tasks')
    .select('*')
    .eq('status', 'active')
    .lte('next_run_at', now)
    .limit(50)

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  // Process each task
  const results = []
  for (const task of tasks || []) {
    // Note: Full execution requires Python for blockchain operations
    // This Edge Function can only mark tasks or call an external endpoint

    // Option A: Mark tasks for processing by the Streamlit app
    await supabase
      .from('scheduled_tasks')
      .update({ status: 'pending_execution' })
      .eq('id', task.id)

    results.push({ task_id: task.id, status: 'queued' })
  }

  return new Response(JSON.stringify({
    processed: results.length,
    results
  }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

Deploy with:
```bash
supabase functions deploy execute-tasks
```

Schedule with pg_cron (in Supabase SQL Editor):
```sql
-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule every minute
SELECT cron.schedule(
  'execute-scheduled-tasks',
  '* * * * *',
  $$
  SELECT net.http_post(
    url := 'https://your-project.supabase.co/functions/v1/execute-tasks',
    headers := '{"Authorization": "Bearer YOUR_SERVICE_KEY"}'::jsonb
  );
  $$
);
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Service role key (bypasses RLS) |
| `SCHEDULER_ENCRYPTION_SECRET` | Yes | Secret for decrypting auto-execution keys |
| `TASK_EXECUTOR_SECRET` | No | Auth token for HTTP endpoint |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## Auto-Execution Setup

For scheduled tasks to execute automatically, users must:

1. **Enable auto-execution in settings:**
   ```python
   # In settings_manager.py
   SettingsManager.update_user_settings(user_id, {
       "auto_execute_scheduled": True
   })
   ```

2. **Store encrypted execution key:**
   ```python
   # When user enables auto-execution
   from utils.encryption import PasswordEncryption

   encrypted_key = PasswordEncryption.encrypt_with_key(
       private_key,
       os.getenv("SCHEDULER_ENCRYPTION_SECRET")
   )

   # Store in user_settings
   supabase.table("user_settings").update({
       "scheduled_tx_private_key_encrypted": encrypted_key
   }).eq("user_id", user_id).execute()
   ```

## Monitoring

### Logs
Check task execution logs:
```bash
# Railway
railway logs

# Fly.io
fly logs

# Local
python scheduler_executor.py --mode worker 2>&1 | tee scheduler.log
```

### Metrics to Track
- Tasks processed per hour
- Success/failure rate
- Average execution time
- Failed task queue size

### Health Check
```bash
curl https://your-scheduler.fly.dev/health
# Returns: {"status": "healthy"}
```

## Troubleshooting

### Tasks not executing
1. Check if tasks have `status = 'active'`
2. Check if `next_run_at` is in the past
3. Verify Supabase connection
4. Check scheduler logs for errors

### Failed transactions
1. Check balance via BalanceService
2. Verify auto-execution is enabled
3. Check encrypted key is valid
4. Review ledger_entries for error details

### High failure rate
- Check if wallet has sufficient gas (for non-testnet)
- Verify RPC endpoints are healthy
- Check for rate limiting

## Security Considerations

1. **Never expose SCHEDULER_ENCRYPTION_SECRET** - This key can decrypt user wallets
2. **Use service key carefully** - It bypasses RLS
3. **Rotate secrets periodically** - Especially if team members leave
4. **Monitor for anomalies** - Set up alerts for unusual task patterns
