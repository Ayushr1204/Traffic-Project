/*
 * ══════════════════════════════════════════════════════════════
 *  NGD Traffic Route Analyzer — Jenkins CI/CD Pipeline
 * ══════════════════════════════════════════════════════════════
 *
 *  Stages:
 *    1. Checkout     — Pull latest code from GitHub
 *    2. Build        — Build Docker images via docker-compose
 *    3. Test         — Run pytest unit tests inside a container
 *    4. Deploy       — Deploy the full stack (Neo4j + Cassandra + App)
 *    5. Verify       — Smoke-test the deployed application
 *
 *  Trigger: Poll SCM every 2 minutes OR manual build
 * ══════════════════════════════════════════════════════════════
 */

pipeline {
    agent any

    triggers {
        // Poll GitHub every 2 minutes for changes
        pollSCM('H/2 * * * *')
    }

    environment {
        COMPOSE_PROJECT_NAME = 'ngd-traffic'
        APP_PORT             = '8501'
        NEO4J_PORT           = '7687'
        CASSANDRA_PORT       = '9042'
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // ─────────────────────────────────────────
        // STAGE 1: Checkout
        // ─────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '════════════════════════════════════════'
                echo '  📥 Stage 1: Pulling latest code'
                echo '════════════════════════════════════════'
                checkout scm
            }
        }

        // ─────────────────────────────────────────
        // STAGE 2: Build
        // ─────────────────────────────────────────
        stage('Build') {
            steps {
                echo '════════════════════════════════════════'
                echo '  🔨 Stage 2: Building Docker images'
                echo '════════════════════════════════════════'
                bat 'docker-compose build --no-cache'
            }
        }

        // ─────────────────────────────────────────
        // STAGE 3: Test
        // ─────────────────────────────────────────
        stage('Test') {
            steps {
                echo '════════════════════════════════════════'
                echo '  🧪 Stage 3: Running unit tests'
                echo '════════════════════════════════════════'
                // Run pytest inside the app image (no DB needed for unit tests)
                bat 'docker-compose run --rm --no-deps -e TESTING=1 app python -m pytest tests/ -v --tb=short'
            }
            post {
                always {
                    echo 'Test stage completed.'
                }
                failure {
                    echo '❌ Tests FAILED — aborting pipeline.'
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 4: Deploy
        // ─────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo '════════════════════════════════════════'
                echo '  🚀 Stage 4: Deploying application'
                echo '════════════════════════════════════════'
                // Tear down any previous deployment
                bat 'docker-compose down --remove-orphans || exit 0'
                // Deploy the full stack
                bat 'docker-compose up -d'
                // Wait for services to stabilize
                bat 'timeout /t 30 /nobreak'
            }
        }

        // ─────────────────────────────────────────
        // STAGE 5: Verify Deployment
        // ─────────────────────────────────────────
        stage('Verify') {
            steps {
                echo '════════════════════════════════════════'
                echo '  ✅ Stage 5: Verifying deployment'
                echo '════════════════════════════════════════'
                // Check if the Streamlit app is responding
                bat 'curl -f http://localhost:%APP_PORT%/_stcore/health || exit 1'
                echo '🎉 Application is live and healthy!'
            }
        }
    }

    post {
        success {
            echo ''
            echo '════════════════════════════════════════════════'
            echo '  ✅ PIPELINE SUCCEEDED'
            echo '  App: http://localhost:8501'
            echo '  Neo4j Browser: http://localhost:7474'
            echo '════════════════════════════════════════════════'
        }
        failure {
            echo ''
            echo '════════════════════════════════════════════════'
            echo '  ❌ PIPELINE FAILED — Check logs above'
            echo '════════════════════════════════════════════════'
            // Clean up on failure
            bat 'docker-compose down --remove-orphans || exit 0'
        }
        always {
            echo 'Pipeline run finished.'
        }
    }
}
