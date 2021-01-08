# AWS Cloud Resource Utils - Library (ACRU-L)

Pronounced _Ah-crew-el (*ə-kroo͞′l*)_

An open source framework for collecting and reusing AWS CDK constructs and stacks.

## Why?
The problem with infrastructure as code ...

Monorepos...
Snowflake code...

Confounding application source code with devops

A strict interface and reuse patterns

## Installation

`poetry add -D acru-l`

`pip install acru-l`

## Usage: ACRU-L Action

This action provisions AWS stacks given an ACRU-L configuration file. The intention is to encapsulate
the code needed to provision resources without conflating application code with devops requirements.

The goal is to avoid conflating microservice application code with "infrastructure as code".

### Inputs

### `subcommand`

**Optional** The aws-cdk subcommand to run. Default `"deploy -f --require-approval=never"`.

## Example usage

```yaml
uses: quadio-media/acru-l-action@v0.1.4
with:
  subcommand: deploy -f
env:
  AWS_REGION: us-east-1
  AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  DEPLOY_ID: ${{ github.sha }}
  ACRUL_CONFIG_PATH: "./acru-l.toml"
```

### Configuration

The following settings must be passed as environment variables as shown in the example. Sensitive information, especially `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, should be [set as encrypted secrets](https://help.github.com/en/articles/virtual-environments-for-github-actions#creating-and-using-secrets-encrypted-variables) — otherwise, they'll be public to anyone browsing your repository's source code and CI logs.

| Key | Value | Suggested Type | Required | Default |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| `AWS_ACCOUNT_ID` | Your AWS Account ID. | `secret env` | **Yes** | N/A |
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key. [More info here.](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html) | `secret env` | **Yes** | N/A |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key. [More info here.](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html) | `secret env` | **Yes** | N/A |
| `AWS_REGION` | The region you want the VPC Stack to live in. | `env` | **Yes** | N/A |
| `COMMIT_SHA` | SHA of the commit that triggered the action. | `env` / `github.sha` | **Yes** | N/A |
| `CONFIG_FILE_PATH` | Path to the ACRU-L configuration file to use. | `env` | No | `./acru-l.toml` |


## License

This project is distributed under the [MIT license](LICENSE).


## About

### Core Concepts

* Resources - Extended constructs
* Services - Collections of Resources that build a service interface
* Stacks - Collections of Services

#### Resources
Extended constructs with set defaults

#### Services

TBD

#### Stacks

TBD
