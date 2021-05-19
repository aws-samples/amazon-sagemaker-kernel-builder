# This is the controller for the light-weight version of the solution. It doesn't use AWS Step Functions 
# to manage a workflow.This option only works if your container can be built and deployed in under
# 15 minutes, which is currently AWS Lambda's maximum execution time

from datetime import datetime
from time import time, sleep
import json

import boto3
import cfnresponse

cb = boto3.client('codebuild')
sm = boto3.client("sagemaker")

def ecr_uri_for_image(repo_name, image_name) :
    
    account_id =  boto3.client('sts').get_caller_identity().get('Account')
    region = boto3.session.Session().region_name
    return f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}:{image_name}"
    
class KernelBuildWorkflow() :
    
    END_STATE = "End"
    SLEEP_INTERVAL = 15 
            
    def __init__(self, config, sm=None, cb=None) :
        
        self.states = ["build"]
        self.results = self._init_results(self.states)
        self.idx = 0
        self.config = config
        
        self.sm = sm if not sm else boto3.client("sagemaker")
        self.cb = cb if not cb else boto3.client("codebuild")
        
    def next(self) :
        self.idx += 1
        
    def update_and_next(self, info) :
        
        if self.complete() :
            return
        
        self.results[self.current()] = info
        self.next()
    
    def current(self) :
        
        if self.idx >= len(self.states) :
            return KernelBuildWorkflow.END_STATE
        else :
            return self.states[self.idx]

    def complete(self) :
        return self.current() == KernelBuildWorkflow.END_STATE
        
    def _set_timeout_budgets(self, available_time_ms, build_time_budget=1.0) :
    
        if build_time_budget > 1 or build_time_budget <= 0 :
            raise Exception(f"build_timeout was set to {build_time_budget}. Expected value greater than 0 and less than one respresenting max percent time allocation for the build phase.")
        
        timeouts = {}
        timeouts["build"] = max(900, int((available_time_ms/1000) * build_time_budget))
    
        return timeouts
    
    def _env_overrides_input(self, env_overrides) :

        env_input = []
        for env in env_overrides.keys() :
            env_input.append({
                "name": env,
                "value": env_overrides[env],
                "type": "PLAINTEXT"
            })

        return env_input

    def _create_kernel_image(self, cb_project, env_overrides, timeout) :
    
        ## limit build execution to once every 100 seconds as a protective
        ## measure for the unexpected.
        token = str(int(datetime.now().timestamp()/100)*100)
 
        start = time()
        response = self.cb.start_build( projectName=cb_project, 
                                        environmentVariablesOverride=self._env_overrides_input(env_overrides),
                                        idempotencyToken=token)
        
        if response :
            build_id = response["build"]["id"]
        else :
            raise Exception("Failed to start the build.")
    
        while True :
        
            info = self.cb.batch_get_builds(ids= [build_id])["builds"][0]
            
            if info :
                status = info["buildStatus"]
                
                if status == 'SUCCEEDED':
                    self.update_and_next({"id":info["id"],"arn":info["arn"],"num":info["buildNumber"], "status":status})
                    break
                elif status == 'FAILED' or status == 'FAULT' or status == 'STOPPED' or status == 'TIMED_OUT':
                    err_msg = f"Build Id: {build_id} Status: {status}"
                    self.update_and_next(err_msg)
                    raise Exception(err_msg)
                
            self._handle_wait(start, timeout)

    def _handle_wait(self, start_time, timeout) :
        
        if (time() - start_time) > timeout :
            msg = f"Build exceeded the timeout of {timeout}s. Allocate more time, or use the workflow-enabled solution if the build exceeds 15 minutes."
            self.update_and_next(msg)
            raise Exception(msg)
        elif (time() - start_time + KernelBuildWorkflow.SLEEP_INTERVAL) < timeout :
            sleep(KernelBuildWorkflow.SLEEP_INTERVAL) 
        else :
            pass

    def run(self) :
        
        cb_project  = self.config["cb_project"]
        env_overrides   = self.config["env_overrides"]
        context     = self.config["context"]
        
        self.timeouts = self._set_timeout_budgets(context.get_remaining_time_in_millis())
        self._create_kernel_image(cb_project, env_overrides, self.timeouts["build"])
        
        return self.results

    @classmethod
    def _init_results(cls, states) :
        results = {}
        for state in states :
            results[state] = None
            
        return results
        
def datetime_to_str(dt):
    if isinstance(dt, datetime):
        return str(dt)

def lambda_handler(event, context):

    wf = None
    try :
        
        properties          = event['ResourceProperties']
        config              = json.loads(properties["config"])
        config["context"]   = context

        wf = KernelBuildWorkflow(config, sm, cb)
        results = wf.run()
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Results": json.dumps(results, default=datetime_to_str)})

    except Exception as e: 
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error":f"{type(e)} {e}"})