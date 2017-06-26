# scrapy-cloud
 Spider on the cloud
 
 This runs a scrapyd server on the Amazon EC2 with a MongoDB database.


### Setup instructions

1. Create a virtual environment and install all the dependencies:

```
pip install -r requirements.txt
```
   
2. TBC

3.Deploy scrapyd to AWS

Check your deployment target:
```
scrapyd-deploy -l
```

Deploy to your local target

```
scrapyd-deploy local-target -p <your_project>
```

