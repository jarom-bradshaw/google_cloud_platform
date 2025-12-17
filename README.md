# Introduction to Google Cloud Platform (GCP) and Publishing your App

Introduction and Directions to get Connected to GCP as a student.  Then an example of how to publish your app.

This material uses [Polars](https://pola-rs.github.io/polars-book/user-guide/) and focuses [Streamlit](https://streamlit.io/) and dash boarding to introduce the data science app development process.

## Challenge General Information

You can read the details of the challenge at [challenge.md](challenge.md)

### Key Items

- __Due Date:__ 12/17/2025
- __Work Rules:__ You cannot work with others.  You can ask any question you want in our general channel. The teacher and TA are the only ones who can answer questions. __You cannot use code from other students' apps.__
- __Product:__ A streamlit app that runs within Docker, builds from your repo, and is published on Google Cloud Platform.
- __Github Process:__ Each student will fork the challenge repository and create their app. Their GitHub repo will have a link to the Cloud Run URL.
- __Canvas Process:__ Each student will upload a `.pdf` or `.html` file with their results as described in [challenge.md](challenge.md)
- Review the [Google Cloud Platform (GCP)](https://github.com/byuibigdata/google_cloud_platform) guide for setup instructions.

### Notes & References

- [Fork a repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
- [Creating a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)

## I added content from other repo to be easier

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

#### Deploying from the Web Terminal with a Github Repo

1. Push your Docker established repository to Github
2. After logging into your account go to the [GCP Console](https://console.cloud.google.com/).
3. Select `Cloud Run` from the hamburger menu on the top left (see [picture](cloudrun.png)).
4. Now you can `Deploy a Web Service` using `Connect repository (Github)`
5. Select your options and connect your repo.
6. Let it build (this can take a few minutes)

You can see this repository's app hosted on Cloud Run [here](https://google-cloud-platform-726715325864.us-west1.run.app/) (assuming I still have some free credits).

## CStore Dashboard Application

### Overview

This Streamlit dashboard analyzes convenience store transaction data for Rigby stores. The application provides four main analytical views:

1. **Top Products** - Identifies the top 5 products by weekly sales (excluding fuels)
2. **Beverage Brands** - Analyzes packaged beverage brands to identify which should be dropped
3. **Payment Comparison** - Compares cash and credit customers across products, amounts, and item counts
4. **Demographics** - Uses Census API to compare demographics around store locations

### Running Locally

1. **Prerequisites:**
   - Docker Desktop installed and running
   - Data files in the `data/` directory (Parquet files)

2. **Start the application:**
   ```bash
   docker compose up
   ```

3. **Access the app:**
   - Open your browser to `http://localhost:8501`

### Data Requirements

The application expects the following data files in the `data/` directory:
- `cstore_stores.parquet` - Store information
- `cstore_store_status.parquet` - Store status
- `cstore_master_ctin.parquet` - Product master data
- `cstore_transaction_sets.parquet` - Transaction basket data
- `cstore_transaction_items/` - Individual transaction items (partitioned)
- `cstore_transactions_daily_agg.parquet` - Daily aggregated data
- `cstore_payments.parquet` - Payment data
- `cstore_discounts.parquet` - Discount data
- `cstore_shopper.parquet` - Shopper data

**Note:** The application automatically filters data to Rigby stores only.

### Census API Configuration

For the Demographics page, you'll need a Census API key:

1. Get a free API key from: https://api.census.gov/data/key_signup.html
2. For local development: Enter the key in the Demographics page
3. For Cloud Run deployment: Add the key to Streamlit secrets:
   - In GCP Cloud Run, go to your service settings
   - Add secret: `CENSUS_API_KEY` with your API key value

### Features

- **Data Caching:** All data operations use Streamlit's `@st.cache_data` for performance
- **Data Validation:** Built-in data quality checks and validation
- **Store Deduplication:** Handles stores with multiple owners/records
- **Interactive Charts:** Plotly charts with user-defined thresholds and lines
- **Great Tables:** Formatted summary tables using Great Tables
- **Multi-page Navigation:** Easy navigation between different analyses
- **Responsive Filters:** Date ranges, store selection, and category filters

### Cloud Run Deployment

1. Push your code to GitHub
2. In GCP Console, go to Cloud Run
3. Click "Deploy a Web Service" → "Connect repository (Github)"
4. Select your repository and branch
5. Configure:
   - Service name
   - Region
   - Port: 8080 (already configured in Dockerfile)
6. Add secrets if using Census API:
   - Secret name: `CENSUS_API_KEY`
   - Value: Your Census API key
7. Deploy and wait for build to complete

### Data Dictionary

See [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md) for complete schema documentation.

### GitHub Repository

[Add your GitHub repository link here]

### Cloud Run URL

[Add your Cloud Run deployment URL here after deployment]

## Visual Studio Code Extensions

You can use [Managing Extensions in Visual Studio Code](https://code.visualstudio.com/docs/editor/extension-marketplace) to learn how to install extensions. [Managing Extensions in Visual Studio Code](https://code.visualstudio.com/docs/editor/extension-marketplace) provides more background on extensions if needed. We will use the following extensions;

- [Python - Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-python.python) extension heavily. 
- [Container Tools](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-containers)
- [Dev Container](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)

## Repository Files

- [Dockerfile](Dockerfile) is the build script for our Docker Image
- [docker-compose.yml](docker-compose.yml) provides an easy way to start our docker container.  [Docker Compose](https://docs.docker.com/compose/#:~:text=It%20is%20the%20key%20to,single%2C%20comprehensible%20YAML%20configuration%20file.) is _'the key to unlocking a streamlined and efficient development and deployment experience.'_
- [requirements.txt](requirements.txt) is run from the [Dockerfile](Dockerfile) and installs the needed Python packages.
- [README.md](README.md) is this file.  The `YAML` at the top is necessary for the Streamlit app to work correctly. Specifically the `app_port: 8501` is needed.  All other information can and should be manipulated.
- [Home.py](Home.py) is our Streamlit app (main dashboard/homepage).
- [utils/data_loader.py](utils/data_loader.py) contains data loading utilities with Rigby store filtering
- [utils/data_validation.py](utils/data_validation.py) contains data quality validation functions
- [pages/](pages/) contains the four dashboard pages:
  - `1_Top_Products.py` - Top 5 products by weekly sales
  - `2_Beverage_Brands.py` - Beverage brand analysis
  - `3_Payment_Comparison.py` - Cash vs Credit comparison
  - `4_Demographics.py` - Store demographics using Census API
- [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md) - Complete data dictionary for the CStore dataset

## References

_I build trainings a bit like AI. I steal a bunch of stuff from other websites.  This is the list of websites I used to train myself._

- [Build a Streamlit App](https://docs.streamlit.io/get-started/tutorials/create-an-app)
- [Google Cloud Get & Redeem Education Credits](https://docs.cloud.google.com/billing/docs/how-to/edu-grants)
- [Google Cloud Redeem Credits](https://docs.cloud.google.com/billing/docs/how-to/edu-grants#redeem)
- [Cloud Run](https://cloud.google.com/run?hl=en)
- [Install the Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install-sdk)
- [Deploying Streamlit to GCP](https://medium.com/bitstrapped/step-by-step-guide-deploying-streamlit-apps-on-google-cloud-platform-gcp-96fca6a4f331)
- [Ship docker to GCP](https://til.simonwillison.net/cloudrun/ship-dockerfile-to-cloud-run)
- [Mapping custom domains](https://docs.cloud.google.com/run/docs/mapping-custom-domains)
[Deploying a Streamlit App to Google Cloud Run](https://medium.com/@afouda.josue/deploying-a-streamlit-app-to-google-cloud-run-using-a-container-based-workflow-with-docker-and-fc9cb67a550a)