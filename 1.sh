docker exec -u 0 -it cicd-jenkins bash -lc '
set -e
mkdir -p /var/jenkins_home/init.groovy.d
cat > /var/jenkins_home/init.groovy.d/01-create-admin.groovy << "EOF"
import jenkins.model.*
import hudson.security.*

def j = Jenkins.get()

// Create local user database and an admin user
def realm = new HudsonPrivateSecurityRealm(false)
if (realm.getUser("admin") == null) {
  realm.createAccount("admin", "EYdWn>DaN*G79gB*")
}
j.setSecurityRealm(realm)

// Grant full control to logged-in users, deny anonymous
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
j.setAuthorizationStrategy(strategy)

j.save()
println(">>> Temporary admin user ready: admin / EYdWn>DaN*G79gB*")
EOF

# Ensure Jenkins (uid 1000) owns the script
chown -R 1000:1000 /var/jenkins_home/init.groovy.d
'

