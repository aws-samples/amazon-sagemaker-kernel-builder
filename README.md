## Amazon SageMaker Kernel Builder

The Amazon SageMaker Kernel Builder is a solution designed to simplify the process of creating and integrating custom environments for Amazon SageMaker Studio. The solution includes multiple deployment options. 

The solution architecture for the full deployment option is as follows:

![architecture](/images/kernel-builder-architecture-full.png)


## Deployment Options

The launch buttons will deploy a sample solution. Follow the [integrator's guide](integrators_guide.pdf) to learn how to tailor the solution to your needs.

| Option | Description | Launch Template |
|--------|-------------|-----------------|
| **End-to-End** | This option provides end-to-end automation. It will provision the solution and build, publish and integrate your environment as defined by your DockerFile and AWS CodeBuild spec into a new Amazon SageMaker Studio environment. This option  is ideal for new accounts and production environments that use CloudFormation to manage all your AWS resources. | <a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-full.yml">![Full-Option](/images/deploy-to-aws.png)</a> |
| **Build and Publish** | This option is designed to work with an existing Amazon SageMaker Studio environment. Like the end-to-end option, it will build and publish your environment. The difference is that it does not create a new Amazon SageMaker Studio domain. | <a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-build-and-publish.yml">![Full-Option](/images/deploy-to-aws.png)</a> |
| **Integrate** | This option takes a pre-built kernel image and makes it accessible within a pre-existing Amazon SageMaker Studio environment. This minimal solution is a good option if your custom kernel is already built and published in an ECR repository like the [ECR Public Gallery](https://gallery.ecr.aws/). | <a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-publish-only.yml">![Full-Option](/images/deploy-to-aws.png)</a> |


## Partner Gallery

| Partner | Description | Launch Template |
|--------|-------------|-----------------|
| **Snowflake Full** | This one-click launch will deploy the end-to-end solution and create a Snowflake kernel within an Amazon SageMaker Studio environment. This kernel includes the [Snowflake Python Connetor](https://docs.snowflake.com/en/user-guide/python-connector.html) and the [Amazon SageMaker SDK](https://sagemaker.readthedocs.io/en/stable/). As a result, it also includes Python 3.7 and the common Python data science libraries pre-installed. | <a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-full.yml">![Full-Option](/images/deploy-to-aws.png)</a> | 
| **Snowflake Plus** | This one-click launch will deploy the "Build and Publish" solution. It is the same as the "Snowflake Full" deployment option except it integrates with an existing Amazon SageMaker Studio environment. | <a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-full.yml">![Full-Option](/images/deploy-to-aws.png)</a> |


## Integrators Guide

Some SaaS providers are interested in providing their customers with an integrated, fully managed data science experience. Follow this [integrator's guide](integrators_guide.pdf) to learn about how this solution can be used to accelerate engineering efforts.

If you are an [AWS Partner](https://aws.amazon.com/partners/) and are interested in using this solution to accelerate your integration, you can reach out to [Dylan Tong](mailto:dylatong@amazon.com) for assistance.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

