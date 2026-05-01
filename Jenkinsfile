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
                runCompose('down --remove-orphans')
                runCompose('up -d')
                runCmd('timeout /t 45 /nobreak', 'sleep 45')
            }
        }

        stage('Verify') {
            steps {
                runCmd(
                    'powershell -NoProfile -Command "$resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing; if ($resp.StatusCode -ne 200) { exit 1 }"',
                    'curl -fsS http://localhost:8501/_stcore/health >/dev/null'
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
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
