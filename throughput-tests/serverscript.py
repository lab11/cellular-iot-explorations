#!/usr/bin/env python3

import flask

app = flask.Flask(__name__)

@app.route('/<int:num>', methods = ['GET', 'POST'])
def data_handle(num):
    if flask.request.method == 'POST':
        print('POST Request, {} bytes'.format(num))
        if (len(flask.request.data) == num):
            print("Good POST")
        else:
            print("Bad POST with {} bytes, expected {}".format(len(flask.request.data), num))
        return ''

    elif flask.request.method == 'GET':
        print('GET Request, {} bytes'.format(num))
        if num < 1 or num > 1000000:
            return ''
        else:
            return 'a'*num

    else:
        print('Some other request??')


if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug = False)

