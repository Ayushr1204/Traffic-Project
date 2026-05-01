def runCmd(String windowsCmd, String unixCmd = null) {
    if (isUnix()) {
        sh(unixCmd ?: windowsCmd)
    } else {
        bat(windowsCmd)
    }
}

def runCompose(String args) {
    if (isUnix()) {
        sh "if command -v docker-compose >/dev/null 2>&1; then docker-compose ${args}; else docker compose ${args}; fi"
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
                // App startup can lag after container reports "running"; use retries.
                runCmd(
                    'powershell -NoProfile -Command "$ok=$false; 1..20 | ForEach-Object { try { $resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing -TimeoutSec 5; if ($resp.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Seconds 3 }; if (-not $ok) { exit 1 }"',
                    'for i in $(seq 1 20); do if curl -fsS http://localhost:8501/_stcore/health >/dev/null; then exit 0; fi; sleep 3; done; exit 1'
                )
                runCompose('ps')
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
