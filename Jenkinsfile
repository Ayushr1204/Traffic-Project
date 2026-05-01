def runCmd(String windowsCmd, String unixCmd = null) {
    if (isUnix()) {
        sh(unixCmd ?: windowsCmd)
    } else {
        bat(windowsCmd)
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
        COMPOSE_CMD          = ''
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

        stage('Prepare Tools') {
            steps {
                script {
                    def hasDockerComposeV2 = (runStatus(
                        '@echo off\r\ndocker compose version >nul 2>&1',
                        'docker compose version >/dev/null 2>&1'
                    ) == 0)
                    env.COMPOSE_CMD = hasDockerComposeV2 ? 'docker compose' : 'docker-compose'
                    echo "Using compose command: ${env.COMPOSE_CMD}"
                }
            }
        }

        stage('Build') {
            steps {
                runCmd('%COMPOSE_CMD% build --pull', "${env.COMPOSE_CMD} build --pull")
            }
        }

        stage('Test') {
            steps {
                // Unit tests do not need Neo4j/Cassandra runtime.
                runCmd(
                    '%COMPOSE_CMD% run --rm --no-deps app python -m pytest tests/ -v --tb=short',
                    "${env.COMPOSE_CMD} run --rm --no-deps app python -m pytest tests/ -v --tb=short"
                )
            }
            post {
                always {
                    runCmd(
                        '%COMPOSE_CMD% down --remove-orphans || exit 0',
                        "${env.COMPOSE_CMD} down --remove-orphans || true"
                    )
                }
            }
        }

        stage('Deploy') {
            steps {
                runCmd('%COMPOSE_CMD% down --remove-orphans || exit 0', "${env.COMPOSE_CMD} down --remove-orphans || true")
                runCmd('%COMPOSE_CMD% up -d', "${env.COMPOSE_CMD} up -d")
                runCmd('timeout /t 45 /nobreak', 'sleep 45')
            }
        }

        stage('Verify') {
            steps {
                runCmd(
                    'powershell -NoProfile -Command "$resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing; if ($resp.StatusCode -ne 200) { exit 1 }"',
                    'curl -fsS http://localhost:8501/_stcore/health >/dev/null'
                )
                runCmd('%COMPOSE_CMD% ps', "${env.COMPOSE_CMD} ps")
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
            runCmd('%COMPOSE_CMD% logs --no-color || exit 0', "${env.COMPOSE_CMD} logs --no-color || true")
            runCmd('%COMPOSE_CMD% down --remove-orphans || exit 0', "${env.COMPOSE_CMD} down --remove-orphans || true")
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
