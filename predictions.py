import boto3
import pandas as pd
from utilities import calculateLength, toTimecode
import requests
from time import localtime, strftime

client = boto3.client('sagemaker-runtime')
endpoint_name = "trial-endpoint-3"
content_type = "text/csv"
accept = "text/csv"
bucket = 'break-data-collection'
s3 = boto3.client('s3')


def getStartAndEnd(prodId):
    """
    Get som and eom for an ID from API
    """
    print('Getting ID timecode information')

    try:
        api = f'https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodId}'
        json = requests.get(api).json()
        info = json['_embedded']['programmeVersions'][0]['partTimes'][0]
        som = info['som']
        eom = info['eom']
    except:
        'API request failed'
        return

    return { 'som': som, 'eom': eom }


def checkCompletion(ID):
    """
    check whether id already analysed
    """
    prefix = f'Predictions/PRED-{ID}.csv'
    response = s3.list_objects_v2(Bucket='break-data-collection', Prefix=prefix, MaxKeys=1)

    if 'Contents' in response:
        for obj in response['Contents']:
            if prefix == obj['Key']:
                return True
            
        return False
    else:
        return False


def main():
    content_list = s3.list_objects_v2(Bucket='break-data-collection', Prefix=f'New/')

    if 'Contents' in content_list:
        for obj in content_list['Contents']:
            if obj['Key'] == 'New/':
                continue
            file = obj['Key'].split('/')[1][:-4]
            if checkCompletion(file):
               print(file, 'predictions already exist')
               continue

            now = strftime("%H:%M:%S", localtime())
            print(now, ': Generating predictions for ' + file)
            s3_object = s3.get_object(Bucket=bucket, Key=f'New/{file}.csv')
            obj = getStartAndEnd(file)
            if obj is None:
                continue
            length = calculateLength(obj)

            df = pd.read_csv(s3_object['Body'])
            df.drop('breaks', axis=1, inplace=True)
            answer_array = []

            print('Beginning inference')

            for index, row in df.iterrows():
                if index < 7500 or index > length - 7500:
                    continue
                if index == length / 2:
                    print('Halfway there!')
                payload = ','.join(map(str, row.values))

                response = client.invoke_endpoint(
                    EndpointName=endpoint_name,
                    ContentType=content_type,
                    Accept=accept,
                    Body=payload
                )
                prediction = response['Body'].read().decode('utf-8').split(',')
                answer = prediction[0]
                prob = prediction[1][:-2]
                if answer == '1' and float(prob) > 0.95:
                    frame = index + 2
                    answer_array.append([frame, prob, toTimecode(frame)])


            predictions_df = pd.DataFrame(answer_array, columns=['Frame', 'Confidence', 'Timecode'])
            predictions_df.to_csv(f'PRED-{file}.csv', index=False)

            s3_upload = boto3.resource('s3')
            s3_upload.Object('break-data-collection', f'Predictions/PRED-{file}.csv').put(Body=open(f'PRED-{file}.csv', 'rb'))
            print(file, 'Predictions uploaded to bucket')



if __name__ == '__main__':
    main()
