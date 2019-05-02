from socket import *
import os
import sys


def getRequestedFile(req: bytes):
    '''
    :param req: header
    :return: requested filename
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'HTTP' in line:
            return line.split()[1]
    return ''


def getHTTPMethod(req: bytes):
    '''
    :param req: header
    :return: HTTP Method (GET, POST, PUT, ...)
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'HTTP' in line:
            return line.split()[0]
    return ''


def getHostandPort(req: bytes):
    '''
    :param req: header
    :return: tuple(hostIP, hostPort)
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'Host' in line:
            return line.split()[1].split(':')[0], line.split()[1].split(':')[1]


def getResponseMsg(statusCode: int, contentLength: int = 0):
    if statusCode == 200:
        return 'HTTP/1.0 {} OK\r\nConnection: close\r\nID: 20165149\r\nName: Taeyoung Kwak\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n'.format(
            statusCode, contentLength).encode()
    elif statusCode == 404:
        return 'HTTP/1.0 {} NOT FOUND\r\nConnection: close\r\nID: 20165149\r\nName: Taeyoung Kwak\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n'.format(
            statusCode, contentLength).encode()


def main(serverPort: int):
    BUF_SIZE = 512
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('localhost', serverPort))
    ### queue up to 1
    serverSocket.listen(1)
    print('Server started, ready to listen')

    while True:
        ### establish a connection
        connectionSocket, addr = serverSocket.accept()

        try:
            serverRecv = connectionSocket.recv(BUF_SIZE)
        except Exception as e:
            print(e)
            continue

        ### ignore favicon request
        if serverRecv == b'':
            continue

        print("\r\n" + serverRecv.decode())
        path = getRequestedFile(serverRecv)
        filename = path[1:]

        ### check HTTP method
        if getHTTPMethod(serverRecv) != 'GET':
            print('Cannot {} {}'.format(getHTTPMethod(serverRecv), path))
            continue
        # hostName, hostPort = getHostandPort(serverRecv)

        ### check file path
        if not os.path.exists(filename):
            statusCode = 404
            connectionSocket.send(getResponseMsg(statusCode))
            print('Server Error : No such file {}!'.format(path))
        else:
            statusCode = 200
            dataTransferred = 0
            contentLength = os.path.getsize(filename)
            connectionSocket.send(getResponseMsg(statusCode, contentLength))
            f = open(filename, 'rb')
            data = f.read(BUF_SIZE)
            while data:
                try:
                    dataTransferred += connectionSocket.send(data)
                    data = f.read(BUF_SIZE)
                except Exception as e:
                    print(e)
            f.close()
            print('finish {} {}'.format(dataTransferred, contentLength))
        connectionSocket.close()
    serverSocket.close()


if __name__ == '__main__':
    main(int(sys.argv[1]))
    # main(10000)
