def runCmd(String windowsCmd, String unixCmd = null) {
    if (isUnix()) {
        sh(unixCmd ?: windowsCmd)
    } else {
        bat(windowsCmd)
    }
}

def runCompose(String args) {
    if (isUnix()) {
        sh "docker compose ${args} || docker-compose ${args}"
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
                runCmd(
                    '%COMPOSE_CMD% run --rm --no-deps app python -m pytest tests/ -v --tb=short',
                    'docker compose run --rm --no-deps app python -m pytest tests/ -v --tb=short || docker-compose run --rm --no-deps app python -m pytest tests/ -v --tb=short'
                )
            }
            post {
                always {
                    runCmd('docker compose down --remove-orphans || docker-compose down --remove-orphans || exit 0',
                           'docker compose down --remove-orphans || docker-compose down --remove-orphans || true')
                }
            }
        }

        stage('Deploy') {
            steps {
                runCmd('docker compose down --remove-orphans || docker-compose down --remove-orphans || exit 0',
                       'docker compose down --remove-orphans || docker-compose down --remove-orphans || true')
                runCmd('docker compose up -d || docker-compose up -d', 'docker compose up -d || docker-compose up -d')
                runCmd('timeout /t 45 /nobreak', 'sleep 45')
            }
        }

        stage('Verify') {
            steps {
                runCmd(
                    'powershell -NoProfile -Command "$resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing; if ($resp.StatusCode -ne 200) { exit 1 }"',
                    'curl -fsS http://localhost:8501/_stcore/health >/dev/null'
                )
                runCmd('docker compose ps || docker-compose ps', 'docker compose ps || docker-compose ps')
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
            runCmd('docker compose logs --no-color || docker-compose logs --no-color || exit 0',
                   'docker compose logs --no-color || docker-compose logs --no-color || true')
            runCmd('docker compose down --remove-orphans || docker-compose down --remove-orphans || exit 0',
                   'docker compose down --remove-orphans || docker-compose down --remove-orphans || true')
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
