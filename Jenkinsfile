pipeline {
    agent any
    triggers {
        cron('0 0 1 * *')
    }
    environment {
        PYTHON_PATH = '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3'
        VENV_DIR = 'virtual_env'
        VENV_BIN = "${VENV_DIR}/bin"
    }
    stages {
        stage('Setup and Run') {
            steps {
                script {
                    sh "${PYTHON_PATH} -m venv ${VENV_DIR}"
                    sh "source ${VENV_BIN}/activate && ${VENV_BIN}/pip3 install -r requirements.txt && ${VENV_BIN}/python3.12 stock_analysis.py"
                }
            }
        }
        
        stage('Push to origin') {
            steps {
                script {
                    sh '''git config user.name "Jenkins"
                          git add -f results.txt
                          git commit -m "Updating results.txt"
                          git push origin HEAD:main
                       '''
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Deactivate virtual environment and clean workspace
                sh "source ${VENV_BIN}/activate && deactivate || true"
                sh "rm -rf ${VENV_DIR}"
                cleanWs()
            }
        }
    }
}
