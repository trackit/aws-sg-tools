# Security Groups compliance checker & Security groups mapping to resources

Those tools allow for auditing and analysing security groups.

Both tools are packaged inside `sg-tools` and can be accessed via subcommands.

The first tool `sg-tools compliance` will check all security rules on VPC to check for rules that are too broad, i.e. rules that allow for connections on all port, with either incomming our outgoing traffic. 

The second tool `sg-tools sgmapping` will create a mapping between security groups and resources, to be able to see which resources has which security groups attached to it.

## Requirements

Below are requirements for a standalone installation. If you wish, a Dockerfile is available to run in a container. Those instructions are available below.

### System packages

The only requirement for the script to work is `Python 2.7`

### Python packages

The python packages dependencies are listed in `requirements.txt`

The only dependency is `boto3`

Dependencies can be installed via :

```
pip install -r requirements.txt
```

## Usage

## Docker container

You will need to have [Docker](https://www.docker.com) installed.

After that, you can build the image from the Dockerfile `docker build -t dockerfile/sgtools .`

You can then run the docker container :
```
docker run -it --rm \
--env AWS_ACCESS_KEY_ID={Your AWS access key} \
--env AWS_SECRET_ACCESS_KEY={Your AWS secret key} \
--env AWS_DEFAULT_REGION={Default region} \
dockerfile/sgtools {Your command}
```

---

The available commands are listed below, they are `sgcompliance` and `sgmapping`

Boto3 will use the credentials configures by AWS CLI. If you do not have credentials setup, you will need to run `aws configure`.

You can specify an aws profile via the option `--profile [PROFILE]`.

You can also run the program against all AWS regions via the option `--all-regions`.

### Sgcompliance

Once your credentials are set just launch the script via `./sg-tools compliance`.

If problematic rules are found, the will be printed on `stdout`. If none are found, the script will not output anything

### Sgmapping

Once your credentials are set, you can launch the script via `./sg-tools mapping [--reverse-direction]`.

The default behaviour is : `Security group XXXXXX mapped to resources X / Y / Z`.

When passing `--reverse-direction` to the program, it will reverse the mapping direction, which will be :
`Resource XXXXXX mapped to security groups X / Y / Z`

It should be noted that, for now, this script will only consider the following resources : `EC2`, `RDS`, `ELB`.

