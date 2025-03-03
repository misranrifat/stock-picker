pipeline {
    agent any
    environment {
        PYTHON_PATH = '/usr/bin/python3'
        VENV_DIR = 'virtual_env'
        VENV_BIN = "${VENV_DIR}/bin"
        GIT_USERNAME = 'misranrifat'
        GIT_EMAIL = '79622206+misranrifat@users.noreply.github.com'
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
                    sh "git add -f results.txt"
                    sh "git -c user.name='${GIT_USERNAME}' -c user.email='${GIT_EMAIL}' commit -m 'Updating results.txt'"
                    sh "git push origin HEAD:main"
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}
