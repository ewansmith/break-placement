import boto3
import pandas as pd
from utilities import calculateLength


client = boto3.client('sagemaker-runtime')
file = '10_0137_0015.003'
obj = { 'som': '10:00:00:00', 'eom': '10:43:08:08' }
length = calculateLength(obj)

df = pd.read_csv(f'{file}.csv')
answer_array = []

endpoint_name = "trial-endpoint-3"
content_type = "text/csv"
accept = "text/csv"  

for index, row in df.iterrows():
    if index < 7500 or index > length - 7500:
        continue
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
    if answer == '1' and float(prob) > 0.8:
        answer_array.append([index + 2, answer, prob])


predictions_df = pd.DataFrame(answer_array)
predictions_df.to_csv(f'PRED-{file}.csv', index=False)

s3_upload = boto3.resource('s3')
s3_upload.Object('break-data-collection', f'PRED-{file}.csv').put(Body=open(f'PRED-{file}.csv', 'rb'))
print(file, 'Predictions uploaded to bucket')

# print(pd.DataFrame(answer_array))
# 16467