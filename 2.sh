CRUMB=$(curl -s -u "admin:119945a0409c8335bfdb889b602739a995" \
  http://localhost:8080/crumbIssuer/api/json | jq -r .crumb)

curl -X POST -u "admin:119945a0409c8335bfdb889b602739a995" \
  -H "Jenkins-Crumb: $CRUMB" \
  "http://localhost:8080/job/build-project/build"

curl "http://localhost:8000/api/jenkins/jobs/build-project/builds?limit=5" | jq -r '.[].url'

