# backend/app/routers/compat.py
from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from urllib.parse import unquote

# Reuse helpers and settings from the dashboard router
from app.routers.dashboard import (
    _get_json, _rewrite, JENKINS_URL, PUBLIC_BASE_URL
)

router = APIRouter()

# --- Legacy endpoint shims -> map to new dashboard logic ---

@router.get("/api/jenkins-node-health")
def legacy_jenkins_node_health():
    """Legacy health card endpoint used by the frontend."""
    data = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name,url]")
    if "__error__" in data:
        return {"status": "DOWN", "reason": data["__error__"], "jobs": 0, "url": PUBLIC_BASE_URL, "port": 8080}
    jobs = data.get("jobs", []) or []
    names = [j.get("name") for j in jobs if isinstance(j, dict) and j.get("name")]
    return {"status": "UP", "jobs": len(names), "url": PUBLIC_BASE_URL, "port": 8080, "jobNames": names}

@router.get("/api/metrics/overall")
@router.get("/analytics/dashboard-summary")
def legacy_overall_metrics():
    """
    Return a superset of summary metrics so different frontends can bind:
      - totalPipelines / pipelinesCount
      - totalBuilds / totalBuildsCount
      - successRate (0..1) + successRatePercent (0..100)
      - successCount / failureCount
      - avgBuildTimeMinutes / avgBuildTimeSeconds
    """
    jobs_doc = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name]")
    if "__error__" in jobs_doc:
        return {
            "totalPipelines": 0, "pipelinesCount": 0,
            "totalBuilds": 0, "totalBuildsCount": 0,
            "successRate": 0.0, "successRatePercent": 0,
            "successCount": 0, "failureCount": 0,
            "avgBuildTimeMinutes": None, "avgBuildTimeSeconds": None,
            "error": jobs_doc["__error__"],
        }

    jobs = jobs_doc.get("jobs", []) or []
    total_pipelines = len(jobs)
    total_builds = 0
    successes = 0
    failures = 0
    durations: List[int] = []

    for j in jobs:
        name = j.get("name")
        if not name:
            continue
        bdoc = _get_json(f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,url,result,duration,timestamp]")
        builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
        total_builds += len(builds)
        for b in builds:
            if not isinstance(b, dict):
                continue
            result = b.get("result")
            if result == "SUCCESS":
                successes += 1
            elif result in ("FAILURE", "FAILED", "UNSTABLE"):
                failures += 1
            d = b.get("duration")
            if isinstance(d, (int, float)) and d >= 0:
                durations.append(int(d))

    success_rate = (successes / total_builds) if total_builds else 0.0
    avg_minutes = (sum(durations) / len(durations) / 60000.0) if durations else None
    avg_seconds = (sum(durations) / len(durations) / 1000.0) if durations else None

    return {
        "totalPipelines": total_pipelines,
        "pipelinesCount": total_pipelines,                 # alias
        "totalBuilds": total_builds,
        "totalBuildsCount": total_builds,                  # alias
        "successRate": success_rate,                       # 0..1
        "successRatePercent": round(success_rate * 100),   # 0..100
        "successCount": successes,
        "failureCount": failures,
        "avgBuildTimeMinutes": avg_minutes,
        "avgBuildTimeSeconds": avg_seconds,
    }

@router.get("/api/failed-builds")
def legacy_failed_builds():
    """Return failed/unstable builds from the last 24h (for the red card/table)."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    items: List[Dict[str, Any]] = []

    jobs_doc = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name]")
    jobs = jobs_doc.get("jobs", []) if isinstance(jobs_doc, dict) else []

    for j in jobs:
        name = j.get("name")
        if not name:
            continue
        bdoc = _get_json(f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,url,result,duration,timestamp]")
        builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
        for b in builds:
            if not isinstance(b, dict):
                continue
            ts = b.get("timestamp")
            result = b.get("result")
            if ts is None or result is None:
                continue
            when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            # consider FAILED/UNSTABLE in last 24h
            if when >= since and result in ("FAILURE", "FAILED", "UNSTABLE"):
                items.append({
                    "job": name,
                    "number": b.get("number"),
                    "result": result,
                    "durationMs": b.get("duration"),
                    "timestamp": ts,
                    "url": _rewrite(b.get("url", "")),
                })
    # newest first
    items.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
    return items

@router.get("/api/pipelines")
def legacy_pipelines():
    """Basic pipelines list (name + url) used by some tables."""
    data = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name,url]")
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out = []
    for j in jobs:
        if not isinstance(j, dict):
            continue
        out.append({
            "name": j.get("name"),
            "url": _rewrite(j.get("url", "")),
        })
    return out

@router.get("/jenkins/jobs")
def legacy_jobs_root():
    """Legacy path some UIs call to fetch Jenkins jobs."""
    data = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name,url,color]")
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    # rewrite URLs for browser
    for j in jobs:
        if isinstance(j, dict) and j.get("url"):
            j["url"] = _rewrite(j["url"])
    return jobs

@router.get("/api/trigger-collection")
def legacy_trigger_collection(manual: int = 0):
    """No-op hook the UI calls; return success so the UI proceeds."""
    return {"status": "ok", "manual": manual}

# --- Extra aliases some frontends use ---

@router.get("/api/metrics")
@router.get("/api/metrics/summary")
def legacy_metrics_alias():
    # reuse the rich object from /api/metrics/overall
    return legacy_overall_metrics()

@router.get("/api/jenkins/health")
@router.get("/api/jenkins/healthz")
def legacy_jenkins_health_alias():
    return legacy_jenkins_node_health()

@router.get("/api/jobs")
def legacy_jobs_alias_simple():
    data = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name,url,color]")
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    for j in jobs:
        if isinstance(j, dict) and j.get("url"):
            j["url"] = _rewrite(j["url"])
    return {
        "jobs": jobs,
        "names": [j.get("name") for j in jobs if isinstance(j, dict) and j.get("name")]
    }

# --- Trend endpoint for charts ---
@router.get("/api/metrics/build-trend")
def legacy_build_trend(windowHours: int = 24):
    """
    Return hourly buckets for the last N hours:
      {
        "buckets": ["2025-08-26T09:00Z", ...],
        "success": [2,1,0,...],
        "failed": [0,0,1,...],
        "avgDurationMs": [6123, 7000, ...]
      }
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=max(1, windowHours))
    # Build empty buckets per hour
    buckets = []
    cursor = start.replace(minute=0, second=0, microsecond=0)
    while cursor <= now:
        buckets.append(cursor)
        cursor += timedelta(hours=1)

    # Aggregate builds
    success_counts = defaultdict(int)
    failed_counts = defaultdict(int)
    duration_sums = defaultdict(int)
    duration_counts = defaultdict(int)

    jobs_doc = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name]")
    jobs = jobs_doc.get("jobs", []) if isinstance(jobs_doc, dict) else []

    for j in jobs:
        name = j.get("name")
        if not name:
            continue
        bdoc = _get_json(f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,result,duration,timestamp]")
        builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
        for b in builds:
            ts = b.get("timestamp")
            if not isinstance(ts, (int, float)):
                continue
            when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            if when < start:
                continue
            bucket_key = when.replace(minute=0, second=0, microsecond=0)
            res = b.get("result")
            if res == "SUCCESS":
                success_counts[bucket_key] += 1
            elif res in ("FAILURE", "FAILED", "UNSTABLE"):
                failed_counts[bucket_key] += 1
            d = b.get("duration")
            if isinstance(d, (int, float)) and d >= 0:
                duration_sums[bucket_key] += int(d)
                duration_counts[bucket_key] += 1

    # Turn maps into aligned arrays
    labels = [b.isoformat().replace("+00:00", "Z") for b in buckets]
    success = [success_counts[b] for b in buckets]
    failed  = [failed_counts[b] for b in buckets]
    avgDur  = [int(duration_sums[b] / duration_counts[b]) if duration_counts[b] else 0 for b in buckets]

    return {"buckets": labels, "success": success, "failed": failed, "avgDurationMs": avgDur}

# --- Per-pipeline builds endpoint expected by UI ---
@router.get("/api/pipelines/{job}/builds")
def legacy_pipeline_builds(job: str, limit: int = 50):
    """
    Returns recent builds for a single pipeline/job.
    Shape:
      [
        { "number": 4, "result": "SUCCESS", "durationMs": 6032, "timestamp": 1756201613111, "url": "http://localhost:8080/job/<job>/4/" },
        ...
      ]
    """
    name = unquote(job)  # handle URL-encoded names (spaces etc.)
    bdoc = _get_json(
        f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,url,result,duration,timestamp]{{0,{limit}}}"
    )

    builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
    out = []
    for b in builds:
        if not isinstance(b, dict):
            continue
        out.append({
            "number": b.get("number"),
            "result": b.get("result"),
            "durationMs": b.get("duration"),
            "timestamp": b.get("timestamp"),
            "url": _rewrite(b.get("url", "")),
        })
    # newest first
    out.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
    return out

