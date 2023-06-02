# py-phoenix-server


# setup development
First let's install the app and run it in CLI or pycharm.

## requirements
- pipenv globally: https://pypi.org/project/pipenv/ (version 2018)
- docker and docker-compose

## run databases / object storage
> $ make run/deps

## setup pipenv
> $ make pipenv/setup

## run app (cli)
> $ make ppserver/run

## run app (pycharm)
You need EnvFile plugin to import dev.env or any other env file


### directory layout
- sdk: all the generic tools that we shouldn't do from scratch and not involve with any domain like adapters including sms, email, one-time password repo.
   - adapters: sms / email sender for different cloud. Object storage interface for different cloud. a lot more.
   - auth: support email and phone sign up / sign in flow
   - storage: support amazon s3, alibaba oss, tencent cos
   - utils: including dependency injection...
- extensions: another layer on top sdk and bring a bit domain to life
   - deployment: is a container for learn, module configs, consent
   - modules: is about gathering patients data
- apps: the thin layer to mix and match the above layer

### Authorization
We are using `IAMBlueprint` to add permission check to each request.
It acts same as `flask.Blueprint` but has some additional functionality.
Whenever you create a new component blueprint, you should use `IAMBlueprint`.
Every blueprint has default policy that will apply to every connected route.
If you want to specify some custom policies, you can wrap your router with `@blueprint.require_policy(policy)`
to append your policy to a default one or `@blueprint.require_policy(policy, overwrite=True)` to overwrite it.
Policy can be PolicyType object, list of policies or function, that returns policy.
NOTE: Make sure any non-public router has at least one policy required (either default or specific one).

### pre-commit hooks

Install pre-commit hooks by running
```sh
> pre-commit install
```
NOTE this needs dev dependencies to work

pre-commit now runs on the commit time. However, you can run it explicitly:

`> pre-commit run`

or run it against all files (this can be destructive)

`> pre-commit run --all-files`


### Testing
Please put all your tests folder either sdk/tests or extensions/tests. And make sure you make another folder
for integration or unittest in modular way.
The structure should look like this
```bash
sdk
├── tests
│   │   ├── <moduleName>
│   │   │   ├── IntegrationTests
│   │   │   └── UnitTests
```

You should use base classes for sdk or extension test cases:
- SdkTestCase
- ExtensionTestCase

located in tests/test_case.py files of sdk/extensions respectively.
Please add both unit and integration test for each new PR.

### naming conventions
- Follow CRUD operation including create/retrieve/update/delete.
So this applies to function naming / swagger file naming / repository naming
- Let’s not have any database logic in router or service. We have to make sure one day if we want
to change repo layer we can.
- Let’s make all the retrieves by POST and apply request object for validation

## Deployment (WIP)

### GCP stack
We use GCP stack driver for now.

#### App Configuration
- It seems self-cert GCP is overalls complicated. So don't use it.
- GCP don't need any extra ingress like nginx-ingress. Just use a NodePort type for service and point ingress to service.
- Use default VPC in GCP
- Use redis in default VPC
- Create k8s in default VPC by rancher
   - Disable logging and monitoring if you would like to get more insight by loki
   - k8s should be in the same region as redis to get access
   - The service account needed by instruction given at creation time via rancher
- Create the bucket and a service account to access it.
   - For now, the service account email should give storage admin access from gcs console to service account (NOTE: email of service account needed)
- Create mongodb atlas cluster in the same region
  - The go to Network Access > VPC Peering and give you GCP VPC details to create peering.
  - Then go GCP > VPC Peering and create a peering by Atlas VPC details.
  - Then add default GCP to whitelist ips.
  - NOTE: it might take a while to connect both VPC
  - READ MORE: https://levelup.gitconnected.com/vpc-peering-between-mongodb-atlas-google-cloud-eec89a261b75
- Run make bootstrap to create namespace, dockercreds inside deploy/ppserver folder
  - > make TLS_NAME=humaappio-tls PRIV_KEY_NAME=star_humaapp.io.key CERT_NAME=star_fullchain_humaapp_io.crt NAMESPACE=sandbox setup/bootstrap
- Install kubeseal client and server: https://github.com/bitnami-labs/sealed-secrets/releases/tag/v0.12.4
- Install secode cli: https://github.com/crtomirmajer/secode
- Run make to create sealed secrets as we need it for later to replace the raw secrets inside deploy/ppserver folder
  - > make SOURCE_SECRET=gcp-sandbox.secret.yaml NAMESPACE=sandbox kubeseal/encrypt
- Run to update your sample sandbox
  - > helmfile -e gcp-global-sandbox -i apply && kc rollout status deployments/ppserver -nsandbox

#### Static Website Configuration
- To serve static content, just add allUsers + Storage  Viewer permission, public key certificate is full chain and certificate chain is crt issued by provider (fullchain == crt+ca-bundle)
- To setup index.html page as default / 404 >
  - > gsutil web set -m index.html -e 404 gs://hu-pp-sandbox-static-bucket
- READ MORE: https://cloud.google.com/storage/docs/hosting-static-website#console_3


#### Operations

##### MongoDB
Dumping hs_sandbox database to gzip file.
> $ mongodump --uri=mongodb+srv://root:<pass>@pp-global-sandbox.1323.gcp.mongodb.net/hs_sandbox --archive=<path_to_archive>/archive_hs_sandbox.gz --gzip -v

Restoring gzip file to localhost mongodb instance. Note that the command restore hs_sandbox and you can't change the database name
> $ mongorestore --uri=mongodb://root:<pass>@localhost:27027 --archive=<path_to_archive>/archive_hs_sandbox.gz --gzip -v

To change the db name on the restore time:
> $ mongorestore --uri=mongodb://root:<pass>@localhost:27027 --archive=<path_to_archive>/archive_hs_sandbox.gz --nsFrom="pp_local_qa.*" --nsTo="pp_qa.*" --gzip -v

##### GCS
Dumping a bucket to a folder. This will create hu-pp-dev-app-bucket into backup.
> $ gsutil -m cp -r gs://hu-pp-dev-app-bucket <a_path>/backup

Restoring the content of a folder to a bucket.
> $ gsutil -m cp -r <a_path>/backup/hu-pp-dev-app-bucket/* gs://hu-europe2-pp-global-sandbox-app-bucket


##### Compressing / Securing backup

##### Ref
- https://severalnines.com/database-blog/tips-storing-mongodb-backups-cloud
- https://gist.github.com/johnsmclay/a8bb33ff46b8cbd84f6f
- https://www.everythingcli.org/secure-mysqldump-script-with-encryption-and-compression
