pipeline {
    agent any
    environment {
        PYTHON_PATH = '/usr/bin/python3'
        VENV_DIR = 'virtual_env'
        VENV_BIN = "${VENV_DIR}/bin"
    }
    stages {
        stage('Setup') {
            steps {
                script {
                    sh "${PYTHON_PATH} -m venv ${VENV_DIR}"

                    sh """
                        . ${VENV_BIN}/activate && \
                        ${VENV_BIN}/pip install -r requirements.txt && \
                        ${VENV_BIN}/python stock_analysis.py
                    """
                }
            }
        }
        
        stage('Push to origin') {
            steps {
                script {
                    sh """
                        git add -f results.txt
                        git commit -m "Updating results.txt"
                        git push origin HEAD:main
                    """
                }
            }
        }
    }
    post {
        always {
            sh "deactivate || true"
            cleanWs()
        }
    }
}
