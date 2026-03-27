import os
import json
from time import sleep
import multiprocessing
import requests

class BuildJob():

    def __init__(self):
        self.JENKINS_URL = "http://<jenkins_url>:8081"
        self.UNAME = "<user_name>"
        self.FULL_JOB_PATH = self.JENKINS_URL + "/job/<foldername>/job/<subfoldername>"    # job in my example present under multiple folders
        self.JOB_NAME = "<job-to-trigger-name>"
        self.TOKEN = "<jenkins-user-token>"
        self.SLEEP_TIME = 10


    def build_jenkin_param_job(self, suite):

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            "Connection": "Keep-Alive",
            "Keep-Alive": "timeout=100, max=1000"
        }

        session = requests.Session()
        session.verify = False
        session.trust_env = False
        os.environ['CURL_CA_BUNDLE']=""
        try:
            response = session.post(f"{self.FULL_JOB_PATH}/job/{self.JOB_NAME}/buildWithParameters?token={self.TOKEN}&suite={suite}",
                                 auth=(self.UNAME, self.TOKEN),headers=headers)
            sleep(5)
            if response.status_code == 201:
                print(f"Started execution of suite: {suite}")
                queue_item_info_end_point = response.headers['Location'] + "api/json"
                print(queue_item_info_end_point)
                try:
                    session = requests.Session()
                    session.verify = False
                    session.trust_env = False
                    response = session.get(queue_item_info_end_point, auth=(self.UNAME, self.TOKEN),headers=headers)
                    if response.status_code == 200:
                        result_dict = json.loads(response.text)

                        while 'executable' not in result_dict:
                            sleep(self.SLEEP_TIME)
                            session = requests.Session()
                            session.verify = False
                            session.trust_env = False
                            response = session.get(queue_item_info_end_point, auth=(self.UNAME, self.TOKEN),headers=headers)
                            result_dict = json.loads(response.text)

                        build_info_end_point = json.loads(response.text)['executable']['url'] + "api/json"
                        print(build_info_end_point)
                        try:
                            session = requests.Session()
                            session.verify = False
                            session.trust_env = False
                            response = session.get(build_info_end_point, auth=(self.UNAME, self.TOKEN),headers=headers)
                            if response.status_code == 200:
                                result_dict = json.loads(response.text)

                                while 'result' not in result_dict:
                                    sleep(self.SLEEP_TIME)
                                    session = requests.Session()
                                    session.verify = False
                                    session.trust_env = False
                                    response = session.get(build_info_end_point, auth=(self.UNAME, self.TOKEN),headers=headers)
                                    result_dict = json.loads(response.text)
                        except Exception as error:
                            print(error)
                            print(f"Unable to get suite: {suite} build details on fly")

                        while (result_dict['result'] == None):
                            sleep(self.SLEEP_TIME)
                            try:
                                session = requests.Session()
                                session.verify = False
                                session.trust_env = False
                                response = session.get(build_info_end_point, auth=(self.UNAME, self.TOKEN),headers=headers)
                                result_dict = json.loads(response.text)
                            except Exception as error:
                                print(error)
                                print(f"Unable to get suite: {suite} execution details on fly")
                                break
                        print(f"Completed execution of suite: {suite}")
                    else:
                        print(f"Failed to get suite: {suite} execution details")
                except Exception as error:
                    print(error)
                    print(f"Unable to get suite: {suite} execution details")
            else:
                print(f"Failed to start execution for suite: {suite}")
        except Exception as error:
            print(error)
            print(f"Unable to start execution for suite: {suite}")

if __name__ == '__main__':
    folder = '.'
    suites = [name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder, name))]

    build_obj = BuildJob()
    pool_obj = multiprocessing.Pool(12)
    ans = pool_obj.map(build_obj.build_jenkin_param_job,suites)
    pool_obj.close()
    pool_obj.join()
