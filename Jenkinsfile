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
                    // Initialize the virtual environment
                    sh "bash -c '${PYTHON_PATH} -m venv ${VENV_DIR}'"
                    
                    // Activate the environment and display Python and pip versions
                    sh "bash -c 'source ${VENV_BIN}/activate && python --version'"
                    sh "bash -c 'source ${VENV_BIN}/activate && which python'"
                    sh "bash -c 'source ${VENV_BIN}/activate && pip --version'"
                    sh "bash -c 'source ${VENV_BIN}/activate && which pip'"
                    
                    // Install dependencies from requirements.txt
                    sh "bash -c 'source ${VENV_BIN}/activate && pip install -r requirements.txt'"

                    // Execute the Python script
                    sh "bash -c 'source ${VENV_BIN}/activate && python stock_analysis.py'"
                }
            }
        }
        
        stage('Push to origin') {
            steps {
                script {
                    // Commit and push changes
                    sh '''
                    bash -c 'git add -f results.txt
                             git commit -m "Updating results.txt"
                             git push origin HEAD:ubuntu'
                    '''
                }
            }
        }
    }
}
