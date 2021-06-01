## Amazon SageMaker Kernel Builder

The Amazon SageMaker Kernel Builder is a solution designed to simplify the process of creating and integrating custom environments for Amazon SageMaker Studio. The solution includes multiple deployment options. 

The solution architecture for the full deployment option is as follows:

![architecture](/images/kernel-builder-architecture-full.png)




### Deployment Options:

1. Full Deployment

   This option does not require pre-existing resources, and it is ideal for new accounts and production environments that use CloudFormation to manage all your AWS resources. 

<a href="https://console.aws.amazon.com/cloudformation/home?region=region#/stacks/new?stackName=kernel-builder&templateURL=https://dtong-public-fileshare.s3-us-west-2.amazonaws.com/kernel-builder/src/deploy/cf/kernel-builder-full.yml">![Full-Option](/images/deploy-to-aws.png)
</a>




## Partner Gallery

TODO: Fill this README out!

Be sure to:

* Change the title in this README
* Edit your repository description on GitHub

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

