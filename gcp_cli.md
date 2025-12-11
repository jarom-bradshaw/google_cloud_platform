_This page is a work in progress_

#### What is Google Cloud CLI

The Google Cloud CLI is Google Cloud’s command-line tool for interacting with Google Cloud resources from terminal. It lets us authenticate, configure projects, and run commands to create, update, and inspect services without using the web console. Please follow the install directions for [Windows](https://docs.cloud.google.com/sdk/docs/install-sdk#windows) or [Mac](https://docs.cloud.google.com/sdk/docs/install-sdk#mac).

After installing the [SDK](https://docs.cloud.google.com/sdk/docs/install-sdk) we should be able to run the following command.

```bash
gcloud init
```

On a Mac, you may need to run `source ~/.zshrc` or restart your terminal.

Now, we need to run to make sure we are connected correctly.

```bash
gcloud services enable run.googleapis.com
```

Now we have our local SDK installed and have access to our CLI into GCP.  Isn't that a mouthful of acronyms.

#### Defining Environment Variables

We can define our cloud region (use `gcloud artifacts locations list` to see the potential regions).

```bash
export REGION=us-west1
```

#### Deploying our Container

```bash
gcloud builds submit --tag "gcr.io/datascience-440222/test"
gcloud run deploy --allow-unauthenticated --platform=managed --image $IMAGE $NAME --memory 2Gi
```
