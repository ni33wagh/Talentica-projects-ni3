from fastapi import APIRouter
from typing import List, Dict, Any
import os, json, base64
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

JENKINS_URL = os.getenv("JENKINS_URL", "http://jenkins:8080").rstrip("/")
JENKINS_USER = os.getenv("JENKINS_USERNAME", "")
JENKINS_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or JENKINS_URL).rstrip("/")

def _auth_headers() -> Dict[str, str]:
    # Preemptive Basic auth so Jenkins doesn’t 403 us before challenging
    b = f"{JENKINS_USER}:{JENKINS_TOKEN}".encode("utf-8")
    return {
        "Accept": "application/json",
        "Authorization": f"Basic {base64.b64encode(b).decode('utf-8')}",
    }

def _get_json(url: str) -> Dict[str, Any]:
    try:
        req = Request(url, headers=_auth_headers())
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        return {"__error__": f"HTTP {e.code} {e.reason}"}
    except URLError as e:
        return {"__error__": f"URL error: {e.reason}"}
    except Exception as e:
        return {"__error__": str(e)}

def _rewrite(u: str) -> str:
    if isinstance(u, str) and u.startswith(JENKINS_URL):
        return u.replace(JENKINS_URL, PUBLIC_BASE_URL, 1)
    return u

@router.get("/health")
def dashboard_health():
    data = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name,url]")
    if "__error__" in data:
        return {"status": "DOWN", "reason": data["__error__"], "jobs": 0, "url": PUBLIC_BASE_URL, "port": 8080}
    jobs = data.get("jobs", []) or []
    names = [j.get("name") for j in jobs if isinstance(j, dict) and j.get("name")]
    return {"status": "UP", "jobs": len(names), "url": PUBLIC_BASE_URL, "port": 8080, "jobNames": names}

@router.get("/summary")
def dashboard_summary():
    jobs_doc = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name]")
    if "__error__" in jobs_doc:
        return {"totalPipelines": 0, "totalBuilds": 0, "successRate": 0.0, "avgBuildTimeMinutes": None, "error": jobs_doc["__error__"]}

    jobs = jobs_doc.get("jobs", []) or []
    total_pipelines = len(jobs)
    total_builds = 0
    successes = 0
    durations_ms: List[int] = []

    for j in jobs:
        name = j.get("name") if isinstance(j, dict) else None
        if not name:
            continue
        bdoc = _get_json(f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,url,result,duration,timestamp]")
        builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
        total_builds += len(builds)
        for b in builds:
            if not isinstance(b, dict):
                continue
            if b.get("result") == "SUCCESS":
                successes += 1
            d = b.get("duration")
            if isinstance(d, (int, float)) and d >= 0:
                durations_ms.append(int(d))

    success_rate = (successes / total_builds) if total_builds else 0.0
    avg_minutes = (sum(durations_ms) / len(durations_ms) / 60000.0) if durations_ms else None
    return {
        "totalPipelines": total_pipelines,
        "totalBuilds": total_builds,
        "successRate": success_rate,
        "avgBuildTimeMinutes": avg_minutes,
    }

@router.get("/recent-builds")
def dashboard_recent_builds(limit: int = 25):
    items: List[Dict[str, Any]] = []
    jdoc = _get_json(f"{JENKINS_URL}/api/json?tree=jobs[name]")
    jobs = jdoc.get("jobs", []) if isinstance(jdoc, dict) else []

    for j in jobs:
        name = j.get("name") if isinstance(j, dict) else None
        if not name:
            continue
        bdoc = _get_json(
            f"{JENKINS_URL}/job/{name}/api/json?tree=builds[number,url,result,duration,timestamp]{{0,{limit}}}"
        )
        builds = bdoc.get("builds", []) if isinstance(bdoc, dict) else []
        for b in builds:
            if not isinstance(b, dict):
                continue
            items.append({
                "job": name,
                "number": b.get("number"),
                "result": b.get("result"),
                "durationMs": b.get("duration"),
                "timestamp": b.get("timestamp"),
                "url": _rewrite(b.get("url", "")),
            })

    items.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
    return items[:limit]

