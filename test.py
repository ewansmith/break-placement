import boto3
import pandas as pd
from utilities import calculateLength
import requests


client = boto3.client('sagemaker-runtime')
endpoint_name = "trial-endpoint-3"
content_type = "text/csv"
accept = "text/csv"
bucket = 'break-data-collection'
files = ['10_0137_0015.003', '10_1779_0014.001', '2_4263_0245.001', '2_4263_0235.001', '2_4263_0247.001']
s3 = boto3.client('s3')


def getStartAndEnd(prodId):
    """
    get som and eom
    """
    try:
        print('Getting content details of ', prodId)
        api = f'https://programmeversionapi.prd.bs.itv.com/programmeVersion/{prodId}'
        json = requests.get(api).json()
        info = json['_embedded']['programmeVersions'][0]['partTimes'][0]
        som = info['som']
        eom = info['eom']
    except Exception as e:
        'Request failed'
        raise(e)

    return { 'som': som, 'eom': eom }


def main():
    for file in files:
        s3_object = s3.get_object(Bucket=bucket, Key=f'{file}.csv')
        obj = getStartAndEnd(file)
        length = calculateLength(obj)

        df = pd.read_csv(s3_object['Body'])
        df.drop('breaks', axis=1, inplace=True)
        answer_array = []

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
                answer_array.append([index + 2, prob])

            # groups = [[nums[0]]]          # first group already has first number
            # for (x, y), d in zip(pairs, diffs):
            #     if d < 10:
            #         groups[-1].append(y)  # add to last group
            #     else:
            #         groups.append([y])    # start new group


        predictions_df = pd.DataFrame(answer_array, columns=['Frame', 'Confidence'])
        predictions_df.to_csv(f'PRED-{file}.csv', index=False)

        s3_upload = boto3.resource('s3')
        s3_upload.Object('break-data-collection', f'PRED-{file}.csv').put(Body=open(f'PRED-{file}.csv', 'rb'))
        print(file, 'Predictions uploaded to bucket')



if __name__ == '__main__':
    main()
## print(pd.DataFrame(answer_array))
## 16467