# Introduction to Google Cloud Platform (GCP) and Publishing your App

Introduction and Directions to get Connected to GCP as a student.  Then an example of how to publish your app.

This material uses [Polars](https://pola-rs.github.io/polars-book/user-guide/) and focuses [Streamlit](https://streamlit.io/) and dash boarding to introduce the data science app development process.

## GCP Setup

### Sign Up

You must have a Google Account to use education credits. If you don't have a Google Account, you can [create one](https://accounts.google.com/signup).

### Get Credits

I will send a message from as follows (except the link will work).

```
Dear Students,

Here is the URL you will need to access in order to request a Google Cloud coupon. You will be asked to provide your school email address and name. An email will be sent to you to confirm these details before a coupon is sent to you.

[Student Coupon Retrieval Link]()

* You will be asked for a name and email address, which needs to match your school domain. A confirmation email will be sent to you with a coupon code.
* You can request a coupon from the URL and redeem it until: 1/8/2026
* Coupon valid through: 9/8/2026
* You can only request ONE code per unique email address.

Thanks,

Mr. John Hathaway
```

After you click on the link, you will get a second email with the code.

```
Dear
Jimmy,

Here is your Google Cloud Coupon Code:
0EV1-U46r-DRTF-F1V6

Click
[here]()
 to redeem.

Course/Project Information
Instructor Name:
Email Address:
School:
Brigham Young University-Idaho
Course/project:
Big Data Programming
Activation Date:
9/8/2025
Redeem By:
1/8/2026
Coupon Valid Through:  9/8/2026

If you have any questions, please contact your course instructor as listed above.

Thanks,
Google Cloud Education Programs Team
```

After clicking the `here` link, you can enter the coupon code to get the credits assigned to your account.

### Setup your GCP app

#### What is Cloud Run

 Cloud Run is a managed compute platform that enables stateless containers which are web accessible. Cloud Run is serverless which allows us to more cost effectively handle infrastructure management (in time and money).

The developer workflow in Cloud Run can be done using VS Code:

1. Containerize an app using Docker and run the container with Docker Desktop
2. Build and test the app locally
3. Push the image to Google Artifact Registry
4. Deploy the containerized app to Cloud Run

With Cloud Run, you can use two types of workflow: container-based workflow or a source-based workflow.[^1] We will be using the __container-based__ workflow.

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

#### Defining Environment Variables and 


## Visual Studio Code Extensions

You can use [Managing Extensions in Visual Studio Code](https://code.visualstudio.com/docs/editor/extension-marketplace) to learn how to install extensions. [Managing Extensions in Visual Studio Code](https://code.visualstudio.com/docs/editor/extension-marketplace) provides more background on extensions if needed. We will use the following extensions;

- [Python - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension heavily. 
- [Container Tools](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-containers)
- [Dev Container](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)



## Repository Files

- The [slides.html](slides.html) is a Remark Slides presentation on Dashboarding.  You can read more at [remark_slides.md](remark_slides.md). The slides are embedded in the default Streamlit app for this repository.
- [Dockerfile](Dockerfile) is the build script for our Docker Image
- [docker-compose.yml](docker-compose.yml) provides an easy way to start our docker container.  [Docker Compose](https://docs.docker.com/compose/#:~:text=It%20is%20the%20key%20to,single%2C%20comprehensible%20YAML%20configuration%20file.) is _'the key to unlocking a streamlined and efficient development and deployment experience.'_
- [requirements.txt](requirements.txt) is run from the [Dockerfile](Dockerfile) and installs the needed Python packages.
- [README.md](README.md) is this file.  The `YAML` at the top is necessary for the Streamlit app to work correctly. Specifically the `app_port: 8501` is needed.  All other information can and should be manipulated.
- [streamlit.py] is our Streamlit app.

## References

- [Build a Streamlit App](https://docs.streamlit.io/get-started/tutorials/create-an-app)
- [Google Cloud Get & Redeem Education Credits](https://docs.cloud.google.com/billing/docs/how-to/edu-grants)
- [Google Cloud Redeem Credits](https://docs.cloud.google.com/billing/docs/how-to/edu-grants#redeem)
- [Cloud Run](https://cloud.google.com/run?hl=en)
- [Install the Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk)

<a href="https://deploy.cloud.run"><img src="https://deploy.cloud.run/button.svg" alt="Run on Google Cloud" height="40"/></a>


[^1] [Deploying a Streamlit App to Google Cloud Run](https://medium.com/@afouda.josue/deploying-a-streamlit-app-to-google-cloud-run-using-a-container-based-workflow-with-docker-and-fc9cb67a550a)