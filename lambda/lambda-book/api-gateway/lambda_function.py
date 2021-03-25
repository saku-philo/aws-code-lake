import json
import boto3
import urllib.parse
import time
import decimal
import base64

# DynamoDB Object
dynamodb = boto3.resource('dynamodb')

# メール送信関数
MAILFROM = 'hoge@gmail.com'


def sendmail(to, subject, body):
    mail_client = boto3.client('ses', region_name='ap-northeast-1')

    response = mail_client.send_email(
        Source=MAILFROM,
        ReplyToAddresses=[MAILFROM],
        Destination={
            'ToAddresses': [to]
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8'
                }
            }
        }
    )

# idのauto incrementを返す関数 アトミックカウンタ
# https://docs.aws.amazon.com/ja_jp/amazondynamodb/latest/developerguide/GettingStarted.Python.03.html#GettingStarted.Python.03.04


def next_seq(table, tablename):
    response = table.update_item(
        Key={
            'tablename': tablename
        },
        UpdateExpression="set seq = seq + :val",
        ExpressionAttributeValues={
            ':val': 1
        },
        ReturnValues="UPDATED_NEW"
    )
    return response['Attributes']['seq']


def lambda_handler(event, context):
    try:
        # シーケンスデータを取得
        seqtable = dynamodb.Table('sequence')
        nextseq = next_seq(seqtable, 'user')

        # フォームの入力データを取得
        # base64decode
        param = base64.b64decode(event['body']).decode()

        # URL decode
        param = urllib.parse.parse_qs(param)

        # get param
        username = param['username'][0]
        email = param['email'][0]

        # クライアントIPの取得
        host = event['requestContext']['http']['sourceIp']

        # 現在のUNIXタイムスタンプを得る
        now = time.time()

        # 署名付きURLの作成
        s3 = boto3.client('s3')
        presigned_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': 'saku-lambda-write-test',
                'Key': 'app.zip'
            },
            ExpiresIn=2 * 60 * 60,
            HttpMethod='GET'
        )

        # userテーブルに登録する
        usertable = dynamodb.Table("user")
        usertable.put_item(
            Item={
                'id': nextseq,
                'username': username,
                'email': email,
                'accepted_at': decimal.Decimal(str(now)),
                'host': host,
                'presigned_url': presigned_url
            }
        )

        # メール送信
        mailbody = """
{0}様

Thank you for register!
Please download file from this URL.

{1}
""".format(username, presigned_url)

        sendmail(email, "Thank you for register!", mailbody)

        # 結果を返す
        return {
            'statusCode': 200,
            'headers': {
                'content-type': 'text/html'
            },
            'body': '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>Thanks for register!</body></html>'
        }
    except:
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'content-type': 'text/html'
            },
            'body': '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>An internal error has occurred.</body></html>'
        }
