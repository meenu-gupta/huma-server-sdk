# Introduction

To streamline local development lifecycle and add ability to deploy code to local and external K8s clusters we advise to adopt lightweight development support tool called Skaffold (https://skaffold.dev/docs/).

# Pre-requisites

* Install `skaffold` - https://skaffold.dev/docs/install/
* Install `kubectl` - https://kubernetes.io/docs/tasks/tools/install-kubectl/
* For local development install local kubernetes cluster:
  * Docker Desktop For Mac (https://hub.docker.com/editions/community/docker-ce-desktop-mac), or 
  * Minikube (https://minikube.sigs.k8s.io/docs/start/)

# Local development

To start quickly and deploy entire application to local kubernetes cluster:

```
skaffold dev --kube-context=docker-desktop
```

Note, the command above will deploy all manifests to local kubernetes cluster defined by passed `--kube-context` flag, to a `default` namespace. In order to deploy to another namespace you'll need to specify `--namespace` option in the command above and also create that first namespace in your local cluster e.g.

```
kubectl --context=docker-desktop create ns <huma-namespace-name>
```

Official docs covering all possible use cases: https://skaffold.dev/docs/workflows/

# Remote clusters

Interaction with remote clusters can be easily defined via Skaffold profiles which are specified in skaffold.yaml configuration file. It's trivial to switch profile in your ongoing development with `--profile / -p` option flag e.g.

```
skaffold dev -p <remote-dev-cluster-profile-name>
```

Command above will use workflow steps specified in provided profile to build, publish and deploy your application artefacts.

More on Skaffold profiles: https://skaffold.dev/docs/environment/profiles/

# Publishing artefacts / Deployments

Skaffold building blocks can be reused in CI/CD pipelines easily and so the tool used for local development can be also used in continuous integration platform of choice. This will ensure consistency and security when publishing and deploying artefacts. 

More on that here: https://skaffold.dev/docs/workflows/ci-cd/
