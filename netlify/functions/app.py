from flask import Flask, render_template, request, jsonify
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app import app

def handler(event, context):
    with app.test_request_context(
        path=event.get('path', ''),
        method=event.get('httpMethod', 'GET'),
        headers=event.get('headers', {}),
        query_string=event.get('queryStringParameters', {})
    ):
        try:
            response = app.full_dispatch_request()
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': str(e)
            }
