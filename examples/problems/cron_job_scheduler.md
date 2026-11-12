# Design exercise: distributed cron / job scheduler

## Prompt

The prompt is pitched as "design CI/CD", but CI/CD is just the workload. The real question: design a system that runs jobs on a schedule (cron expressions) and on demand, at large scale (tens of millions of jobs).

## Questions to cover

- How scheduled tasks get **triggered**: computing the next fire time, and how the trigger loop finds due jobs.
- The **task queue** and how work is **dispatched to workers**.
- Handling **worker failure**: heartbeats, leases, re-queueing.

## Your checklist

1. API: create/update/delete a job (cron expression, time zone, payload, retry policy) and trigger one now.
2. Storage: a job table plus a `next_fire_at` index. Calculate the next fire time when a job is created and after every run.
3. Trigger loop: partition jobs by shard, and give each scheduler instance a shard lease. Every tick, poll `next_fire_at <= now`. Explain how you avoid double-firing across instances.
4. Queue: delivery is at-least-once, so tasks must be idempotent (an idempotency key per run). Cover retry with backoff and a dead-letter queue.
5. Workers: lease and visibility timeout, heartbeats, and re-queueing on expiry. Cover concurrency limits per tenant.
6. Edge cases: misfires after downtime (catch up or skip), DST and time zones, long-running jobs overlapping their next run.
7. Dependencies (a DAG, for CI pipelines), job history and logs, and observability.
