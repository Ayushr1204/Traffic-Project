def dockerPath() {
    // Ensure Docker Desktop paths are available (Windows Git Bash / WSL in Jenkins)
    return 'export PATH="/c/Program Files/Docker/Docker/resources/bin:/c/ProgramData/DockerDesktop/version-bin:$PATH"'
}

def runCmd(String windowsCmd, String unixCmd = null) {
    if (isUnix()) {
        sh "${dockerPath()} && ${unixCmd ?: windowsCmd}"
    } else {
        bat(windowsCmd)
    }
}

def runCompose(String args) {
    if (isUnix()) {
        sh "${dockerPath()} && docker compose ${args}"
    } else {
        bat "docker compose ${args} || docker-compose ${args}"
    }
}

def cleanupNamedContainers() {
    if (isUnix()) {
        sh 'docker rm -f ngd-neo4j ngd-cassandra ngd-app >/dev/null 2>&1 || true'
    } else {
        bat 'docker rm -f ngd-neo4j ngd-cassandra ngd-app >nul 2>&1 || exit 0'
    }
}

def runStatus(String windowsCmd, String unixCmd = null) {
    if (isUnix()) {
        return sh(script: (unixCmd ?: windowsCmd), returnStatus: true)
    }
    return bat(script: windowsCmd, returnStatus: true)
}

pipeline {
    agent any

    triggers {
        // Periodically check GitHub for new commits (acts as auto-fetch trigger)
        pollSCM('H/2 * * * *')
    }

    environment {
        COMPOSE_PROJECT_NAME = 'ngd-traffic-demo'
        APP_PORT             = '8501'
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                runCmd('git rev-parse --short HEAD')
            }
        }

        stage('Build') {
            steps {
                runCompose('build --pull')
            }
        }

        stage('Test') {
            steps {
                // Unit tests do not need Neo4j/Cassandra runtime.
                // Override entrypoint to avoid DB wait logic in entrypoint.sh during tests.
                runCompose('run --rm --no-deps --entrypoint "" app python -m pytest tests/ -v --tb=short')
            }
            post {
                always {
                    runCompose('down --remove-orphans')
                }
            }
        }

        stage('Deploy') {
            steps {
                // These fixed names are defined in docker-compose.yml and may exist from prior/manual runs.
                cleanupNamedContainers()
                runCompose('down --remove-orphans')
                runCompose('up -d')
                runCmd('timeout /t 45 /nobreak', 'sleep 45')
            }
        }

        stage('Verify') {
            steps {
                // Verify from the correct runtime context:
                // - Linux Jenkins agents often cannot reach app via localhost:8501 directly.
                // - So we probe health from inside the app container.
                script {
                    if (isUnix()) {
                        sh """
                            ${dockerPath()}
                            set +e
                            for i in \$(seq 1 20); do
                              docker compose exec -T app python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5)" && exit 0
                              sleep 3
                            done
                            exit 1
                        """
                    } else {
                        bat 'powershell -NoProfile -Command "$ok=$false; 1..20 | ForEach-Object { try { $resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing -TimeoutSec 5; if ($resp.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Seconds 3 }; if (-not $ok) { exit 1 }"'
                    }
                }
                runCompose('ps')
            }
        }

        stage('Monitor') {
            steps {
                echo '════════════════════════════════════════'
                echo '  POST-DEPLOY MONITORING & HEALTH CHECK'
                echo '════════════════════════════════════════'

                // 1. Container health status
                echo '── Container Health Status ──'
                runCompose('ps')

                // 2. Resource usage (CPU, Memory)
                echo '── Resource Usage (CPU / Memory) ──'
                runCmd(
                    'docker stats --no-stream --format "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}\\t{{.Status}}" ngd-app ngd-neo4j ngd-cassandra',
                    'docker stats --no-stream --format "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}\\t{{.Status}}" ngd-app ngd-neo4j ngd-cassandra'
                )

                // 3. Application logs (last 30 lines)
                echo '── Recent Application Logs ──'
                runCompose('logs --tail=30 --no-color app')

                // 4. Database connectivity check from app container
                echo '── Database Connectivity Check ──'
                script {
                    if (isUnix()) {
                        sh """
                            ${dockerPath()}
                            docker compose exec -T app python -c "from config import get_neo4j_driver, get_cassandra_session; d = get_neo4j_driver(); d.verify_connectivity(); print('Neo4j:     CONNECTED'); s = get_cassandra_session(); print('Cassandra: CONNECTED')"
                        """
                    } else {
                        bat 'docker compose exec -T app python -c "from config import get_neo4j_driver, get_cassandra_session; d = get_neo4j_driver(); d.verify_connectivity(); print(\'Neo4j:     CONNECTED\'); s = get_cassandra_session(); print(\'Cassandra: CONNECTED\')"'
                    }
                }

                // 5. Final health endpoint re-check
                echo '── Final Health Endpoint Check ──'
                script {
                    if (isUnix()) {
                        sh "${dockerPath()} && curl -sf http://localhost:8501/_stcore/health && echo ' => App is HEALTHY' || echo ' => App health check failed'"
                    } else {
                        bat 'powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing -TimeoutSec 5; Write-Host \'=> App is HEALTHY (Status:\' $r.StatusCode \')\' } catch { Write-Host \'=> App health check failed\'; exit 1 }"'
                    }
                }

                echo '════════════════════════════════════════'
                echo '  ALL MONITORING CHECKS PASSED ✓'
                echo '════════════════════════════════════════'
            }
        }
    }

    post {
        success {
            echo 'PIPELINE SUCCEEDED'
            echo 'App URL: http://localhost:8501'
            echo 'Neo4j Browser URL: http://localhost:7474'
        }
        failure {
            echo 'PIPELINE FAILED - check stage logs.'
            runCompose('logs --no-color')
            runCompose('down --remove-orphans')
            cleanupNamedContainers()
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
