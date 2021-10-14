import feedparser
import os
import boto3
import json
from packaging import version
class BotoClients:
    ssm = boto3.client('ssm')
    sns = boto3.client('sns')
def on_event(event, context):
    CDK_RSS_LINK = os.environment['CDK_RSS_LINK']   #"https://github.com/aws/aws-cdk/releases.atom"
    SNS_TOPIC_ARN = os.environment['SNS_TOPIC_ARN']
    SSM_PARAMETER = os.environ['SSM_PARAMETER']     #/cdk1/version
    # get current version:
    our_current_version = json.loads(
        BotoClients.ssm.get_parameter(
            Name = SSM_PARAMETER
        )
    )
    # get the version from RSS/Atom feed. 
    try:
        poll_response = feedparser.parse(CDK_RSS_LINK)
        rss_current_version = {
            "title": poll_response.entries[0].title,
            "updated": poll_response.entries[0].updated,
            "link": poll_response.entries[0].link
        }
    except:
        raise ValueError('RSSfeed-Failed')  
    #compare versions to see if there as been an update.
    if version.parse(rss_current_version['title'].split('v')[1]) > version.parse(our_current_version['title'].split('v')[1]):
        # update SSM Parameter
        BotoClients.ssm.put_parameter(
            Name = SSM_PARAMETER,
            Description = 'Current CDK Version',
            Type = 'String',
            Overwrite = True,
            Value = json.dumps(rss_current_version)
        )
        # Send SNS Message
        BotoClients.sns.publish(
            TopicArn = SNS_TOPIC_ARN,
            Subject = f"aws-cdk version {rss_current_version['title']} released",
            Message = json.dumps(rss_current_version),
        )