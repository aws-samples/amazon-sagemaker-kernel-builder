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
    
class KernelCreationWorkflow() :
    
    END_STATE = "End"
    SLEEP_INTERVAL = 15 
            
    def __init__(self, config, sm=None, cb=None) :
        
        self.states = ["build", "create_image", "create_image_ver", "config_app_image", "update_domain"]
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
            return KernelCreationWorkflow.END_STATE
        else :
            return self.states[self.idx]

    def complete(self) :
        return self.current() == KernelCreationWorkflow.END_STATE
        
    def _set_timeout_budgets(self, available_time_ms, build_time_budget=1.0) :
    
        if build_time_budget > 1 or build_time_budget <= 0 :
            raise Exception(f"build_timeout was set to {build_time_budget}. Expected value greater than 0 and less than one respresenting max percent time allocation for the build phase.")
        
        timeouts = {}
        timeouts["build"] = int((available_time_ms/1000) * build_time_budget)
        timeouts["publish"] = min(600, int((available_time_ms/1000) * 0.9))
    
        return timeouts
    
    def _create_kernel_image(self, cb_project, timeout) :
    
        ## limit build execution to once every 100 seconds as a protective
        ## measure for the unexpected.
        token = str(int(datetime.now().timestamp()/100)*100)
        
        start = time()
        response = self.cb.start_build(projectName=cb_project, idempotencyToken=token)
        
        if response :
            build_id = response["build"]["id"]
        else :
            raise Exception("Failed to start the build.")
    
        while True :
        
            info = self.cb.batch_get_builds(ids= [build_id])["builds"][0]
            
            if info :
                status = info["buildStatus"]
                
                if status == 'SUCCEEDED':
                    self.update_and_next(info)
                    break
                elif status == 'FAILED' or status == 'FAULT' or status == 'STOPPED' or status == 'TIMED_OUT':
                    self.update_and_next(info)
                    raise Exception(f"Build Id: {build_id} Status: {status}")
                
            self._handle_wait(start, timeout)

    def _handle_wait(self, start_time, timeout) :
        
        if (time() - start_time) > timeout :
            self.update_and_next(info)
            raise Exception(f"Build exceeded the timeout of {timeout}s. Allocate more time, or use the workflow-enabled solution if the build exceeds 15 minutes.")
        elif (time() - start_time + KernelCreationWorkflow.SLEEP_INTERVAL) < timeout :
            sleep(KernelCreationWorkflow.SLEEP_INTERVAL) 
        else :
            pass
    
    def _create_sagemaker_image(self, image_name, role, timeout, start_time) :

        try :
            info = self.sm.describe_image(ImageName=image_name)
            
            if info :
                self.sm.update_image(ImageName = image_name,
                                    RoleArn = role)
            else :
                self.sm.create_image(ImageName = image_name,
                                    RoleArn = role)
                                                                    
        except :
            self.sm.create_image(ImageName = image_name,
                                RoleArn = role)
                                        
        while(True) :
            
            info = self.sm.describe_image(ImageName=image_name)
            
            if info["ImageStatus"] == "CREATED" :
                self.update_and_next(info)
                break
            elif info["ImageStatus"] == "CREATE_FAILED" or \
                 info["ImageStatus"] == "UPDATE_FAILED" or \
                 info["ImageStatus"] == "DELETE_FAILED" or \
                 info["ImageStatus"] == "DELETING" : 
                self.update_and_next(info)
                raise Exception(f"Failed to create SageMaker image: {info}.")    
            else :
                self._handle_wait(start_time, timeout)

    def _create_sagemaker_image_version(self, image_name, ecr_uri, timeout, start_time) :
        
        self.sm.create_image_version(BaseImage = ecr_uri,
                                    ImageName = image_name)
        
        version = None
        while(True) :
            
            info = self.sm.describe_image_version(ImageName=image_name)
            
            if info["ImageVersionStatus"] == "CREATED" :
                self.update_and_next(info)
                version = info["Version"]
                break
            elif info["ImageVersionStatus"] == "CREATE_FAILED" or \
                 info["ImageVersionStatus"] == "DELETE_FAILED" or \
                 info["ImageVersionStatus"] == "DELETING" : 
                self.update_and_next(info)
                raise Exception(f"Failed to create SageMaker image version: {info}.")    
            else :
                self._handle_wait(start_time, timeout)
                
        return version
    
    def _create_app_config(self, app_image_config) :
        
        image_config = app_image_config["AppImageConfigName"]
        kgw_config = app_image_config["KernelGatewayImageConfig"]
        
        try :
            
            info = self.sm.describe_app_image_config(AppImageConfigName=image_config)
            
            if info :
                info = self.sm.update_app_image_config( AppImageConfigName=image_config,
                                                        KernelGatewayImageConfig=kgw_config)    
            else :
                info = self.sm.create_app_image_config( AppImageConfigName=image_config,
                                                        KernelGatewayImageConfig=kgw_config)
                
        except :
            info = self.sm.create_app_image_config( AppImageConfigName=image_config,
                                                    KernelGatewayImageConfig=kgw_config)
            
        self.update_and_next(info)
        
    def _update_container_config_ver(self, images, image_name, app_config_name, version) :
        
        for image in images :
            if image["ImageName"] == image_name and image["AppImageConfigName"] == app_config_name:
                image["ImageVersionNumber"] = version
        
    def _update_studio_domain(self, update_domain_input, timeout, start_time) :
        
        domain_id = update_domain_input["DomainId"]
        defaults = update_domain_input["DefaultUserSettings"]
        
        self.sm.update_domain(  DomainId = domain_id,
                                DefaultUserSettings = defaults)
        
        while(True) :
            
            info = self.sm.describe_domain(DomainId = domain_id)
            if info["Status"] == "InService" :
                
                self.update_and_next(info)
                break
            
            elif info["Status"] == "Failed" or \
                 info["Status"] == "Deleting" or \
                 info["Status"] == "Update_Failed" or \
                 info["Status"] == "Delete_Failed" : 
                
                self.update_and_next(info)
                raise Exception(f"Failed to update SageMaker Domain: {info}.")    
            
            else :
                self._handle_wait(start_time, timeout)
            

    def _publish_image_to_studio(self, repo_name, image_name, role, app_image_config, update_domain_input, timeout) :
        
        start= time()
        self._create_sagemaker_image(image_name, role, timeout, start)
            
        ecr_uri = ecr_uri_for_image(repo_name, image_name)
        image_version = self._create_sagemaker_image_version(image_name, ecr_uri, timeout, start)
        
        images = update_domain_input["DefaultUserSettings"]["KernelGatewayAppSettings"]["CustomImages"]
        app_config_name = app_image_config["AppImageConfigName"]
        self._update_container_config_ver(images, image_name, app_config_name, image_version)
 
        self._create_app_config(app_image_config)
        self._update_studio_domain(update_domain_input, timeout, start)

    def run(self) :
        
        cb_project          = self.config["cb_project"]
        ecr_repo_name       = self.config["ecr_repo_name"] 
        image_name          = self.config["image_name"]
        image_permissions   = self.config["image_permissions"]
        build_time_budget   = self.config["build_time_budget"]
        app_image_config    = self.config["app_image_config"]
        update_domain_input = self.config["update_domain_input"]
        context             = self.config["context"]
        
        self.timeouts = self._set_timeout_budgets(  context.get_remaining_time_in_millis(), 
                                                    build_time_budget)
        
        self._create_kernel_image(cb_project, self.timeouts["build"])
        
        self._publish_image_to_studio(  ecr_repo_name, 
                                        image_name, 
                                        image_permissions, 
                                        app_image_config, 
                                        update_domain_input, 
                                        self.timeouts["publish"])
        
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

        wf = KernelCreationWorkflow(config, sm, cb)
        results = wf.run()
        
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Results": json.dumps(results, default=datetime_to_str)})

    except Exception as e: 
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error":f"{type(e)} {e}"})