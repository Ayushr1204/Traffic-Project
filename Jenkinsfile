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
                bat 'git rev-parse --short HEAD'
            }
        }

        stage('Prepare Tools') {
            steps {
                script {
                    def hasDockerComposeV2 = (bat(
                        returnStatus: true,
                        script: '@echo off\r\ndocker compose version >nul 2>&1'
                    ) == 0)
                    env.COMPOSE_CMD = hasDockerComposeV2 ? 'docker compose' : 'docker-compose'
                    echo "Using compose command: ${env.COMPOSE_CMD}"
                }
            }
        }

        stage('Build') {
            steps {
                bat '%COMPOSE_CMD% build --pull'
            }
        }

        stage('Test') {
            steps {
                // Unit tests do not need Neo4j/Cassandra runtime.
                bat '%COMPOSE_CMD% run --rm --no-deps app python -m pytest tests/ -v --tb=short'
            }
            post {
                always {
                    bat '%COMPOSE_CMD% down --remove-orphans || exit 0'
                }
            }
        }

        stage('Deploy') {
            steps {
                bat '%COMPOSE_CMD% down --remove-orphans || exit 0'
                bat '%COMPOSE_CMD% up -d'
                bat 'timeout /t 45 /nobreak'
            }
        }

        stage('Verify') {
            steps {
                bat 'powershell -NoProfile -Command "$resp = Invoke-WebRequest -Uri http://localhost:%APP_PORT%/_stcore/health -UseBasicParsing; if ($resp.StatusCode -ne 200) { exit 1 }"'
                bat '%COMPOSE_CMD% ps'
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
            bat '%COMPOSE_CMD% logs --no-color || exit 0'
            bat '%COMPOSE_CMD% down --remove-orphans || exit 0'
        }
        always {
            echo 'Pipeline execution finished.'
        }
    }
}
