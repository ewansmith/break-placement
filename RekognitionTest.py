import boto3
import json
import sys
import time

session = boto3.Session(profile_name='content', region_name='eu-west-1')


class VideoDetect:
    jobId = ''
    # rek = boto3.client('rekognition')
    # sqs = boto3.client('sqs')
    # sns = boto3.client('sns')
    rek = session.client('rekognition')
    sqs = session.client('sqs')
    sns = session.client('sns')
    
    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''
    

    def __init__(self, role, bucket, video):    
        self.roleArn = role
        self.bucket = bucket
        self.video = video

    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False
    
        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)

            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                   ReceiptHandle=message['ReceiptHandle'])


        return succeeded

       
    
    def CreateTopicandQueue(self):
      
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        
        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']
        
        # self.snsTopicArn = 'arn:aws:sns:eu-west-2:315961771263:AmazonRekognitionTest'

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        # self.sqsQueueUrl = 'https://sqs.eu-west-2.amazonaws.com/315961771263/rek-test'
 
        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        # sqsQueueArn = 'arn:aws:sqs:eu-west-2:315961771263:rek-test'
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)
 
        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)
        
    def StartSegmentDetection(self):

        min_Technical_Cue_Confidence = 80
        min_Shot_Confidence = 80
        max_pixel_threshold = 0.1
        min_coverage_percentage = 95

        response = self.rek.start_segment_detection(
            Video={"S3Object": {"Bucket": self.bucket, "Name": self.video}},
            NotificationChannel={
                "RoleArn": self.roleArn,
                "SNSTopicArn": self.snsTopicArn,
            },
            SegmentTypes=["TECHNICAL_CUE"],#, "SHOT"],
            # Filters={
            #     "TechnicalCueFilter": {
            #         "BlackFrame": {
            #             # "MaxPixelThreshold": max_pixel_threshold,
            #             "MinCoveragePercentage": min_coverage_percentage,
            #         },
            #         "MinSegmentConfidence": min_Technical_Cue_Confidence,
            #     },
                # "ShotFilter": {"MinSegmentConfidence": min_Shot_Confidence},
            # }
        )

        self.startJobId = response["JobId"]
        print(f"Start Job Id: {self.startJobId}")

    def GetSegmentDetectionResults(self):
        maxResults = 1000
        paginationToken = ""
        finished = False
        firstTime = True

        segmentEnds = []

        while finished == False:
            response = self.rek.get_segment_detection(
                JobId=self.startJobId, MaxResults=maxResults, NextToken=paginationToken
            )

            if firstTime == True:
                print(f"Status\n------\n{response['JobStatus']}")
                print("\nRequested Types\n---------------")
                for selectedSegmentType in response['SelectedSegmentTypes']:
                    print(f"\tType: {selectedSegmentType['Type']}")
                    # print(f"\t\tModel Version: {selectedSegmentType['ModelVersion']}")

                print()
                # print("\nAudio metadata\n--------------")
                # for audioMetadata in response['AudioMetadata']:
                #     print(f"\tCodec: {audioMetadata['Codec']}")
                #     print(f"\tDuration: {audioMetadata['DurationMillis']}")
                #     print(f"\tNumber of Channels: {audioMetadata['NumberOfChannels']}")
                #     print(f"\tSample rate: {audioMetadata['SampleRate']}")
                # print()
                # print("\nVideo metadata\n--------------")
                # for videoMetadata in response["VideoMetadata"]:
                #     print(f"\tCodec: {videoMetadata['Codec']}")
                #     print(f"\tColor Range: {videoMetadata['ColorRange']}")
                #     print(f"\tDuration: {videoMetadata['DurationMillis']}")
                #     print(f"\tFormat: {videoMetadata['Format']}")
                #     print(f"\tFrame rate: {videoMetadata['FrameRate']}")
                #     print("\nSegments\n--------")

                firstTime = False

            for segment in response['Segments']:

                if segment["Type"] == "TECHNICAL_CUE":
                    print("Technical Cue")
                    print(f"\tConfidence: {segment['TechnicalCueSegment']['Confidence']}")
                    print(f"\tType: {segment['TechnicalCueSegment']['Type']}")

                if segment["Type"] == "SHOT":
                    print("Shot")
                    print(f"\tConfidence: {segment['ShotSegment']['Confidence']}")
                    print(f"\tIndex: " + str(segment["ShotSegment"]["Index"]))

                # print(f"\tDuration (milliseconds): {segment['DurationMillis']}")
                # print(f"\tStart Timestamp (milliseconds): {segment['StartTimestampMillis']}")
                # print(f"\tEnd Timestamp (milliseconds): {segment['EndTimestampMillis']}")
                
                print(f"\tStart timecode: {segment['StartTimecodeSMPTE']}")
                print(f"\tEnd timecode: {segment['EndTimecodeSMPTE']}")
                # print(f"\tDuration timecode: {segment['DurationSMPTE']}")

                # print(f"\tStart frame number {segment['StartFrameNumber']}")
                # print(f"\tEnd frame number: {segment['EndFrameNumber']}")
                segmentEnds.append(segment['EndFrameNumber'])
                # print(f"\tDuration frames: {segment['DurationFrames']}")

                print()

            if "NextToken" in response:
                paginationToken = response["NextToken"]
            else:
                finished = True

        return segmentEnds


def getRekResults(bucket='soft-parted-examples', video='LOWRES_2-4259-0359-001.mp4'):
    roleArn = 'arn:aws:iam::315961771263:role/RekRole'

    analyzer=VideoDetect(roleArn, bucket, video)
    analyzer.CreateTopicandQueue()

    analyzer.StartSegmentDetection()
    if analyzer.GetSQSMessageSuccess()==True:
        results = analyzer.GetSegmentDetectionResults()
    
    analyzer.DeleteTopicandQueue()

    return results


if __name__ == "__main__":
    getRekResults('soft-parted-examples', 'no_sound.mp4')