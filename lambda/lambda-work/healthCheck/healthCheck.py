# -*- coding: utf-8 -*-
# import subprocess
import commands
import os

print('Loading function')


def _(cmd):
    return commands.getoutput(cmd)


def lambda_handler(event, context):
    ok_string = "health check OK"
    ng_string = "health check NG"

    # 確認するパス
    curl_cmd = 'curl -I {url} -w \'%{http_code}\\n\' -s'
    curl_cmd = curl_cmd.format(url=os.environ['URL'], http_code='{http_code}')

    #curlコマンド実行
    response = _(curl_cmd)

    print("------------response start--------------")
    print(curl_cmd)
    print(response)
    print("------------response end----------------")

    #httpステータス判定
    if response.endswith("200"):
        print("HTTP status is 200")
        return {"result": ok_string}
    else:
        print("HTTP status is not 200")
        return {"result": ng_string}
