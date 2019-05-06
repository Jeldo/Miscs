from socket import *
import os
import sys


def get_requested_file(req: bytes):
    '''
    :param req: header
    :return: requested filename
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'HTTP' in line:
            return line.split()[1]
    return ''


def get_HTTP_method(req: bytes):
    '''
    :param req: header
    :return: HTTP Method (GET, POST, PUT, ...)
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'HTTP' in line:
            return line.split()[0]
    return ''


def get_host_and_port(req: bytes):
    '''
    :param req: header
    :return: tuple(hostIP, hostPort)
    '''
    req = req.decode()
    for line in req.split('\r\n'):
        if 'Host' in line:
            return line.split()[1].split(':')[0], line.split()[1].split(':')[1]


def get_response_msg(status_code: int, content_length: int = 0):
    if status_code == 200:
        return 'HTTP/1.0 {} OK\r\nConnection: close\r\nID: 20165149\r\nName: Taeyoung Kwak\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n'.format(
            status_code, content_length).encode()
    elif status_code == 404:
        return 'HTTP/1.0 {} NOT FOUND\r\nConnection: close\r\nID: 20165149\r\nName: Taeyoung Kwak\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n'.format(
            status_code, content_length).encode()


def main(server_port: int):
    BUF_SIZE = 512
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('localhost', server_port))
    ### queue up to 1
    server_socket.listen(1)
    print('Server started, ready to listen')

    while True:
        ### establish a connection
        connection_socket, addr = server_socket.accept()
        try:
            serverRecv = connection_socket.recv(BUF_SIZE)
        except Exception as e:
            print(e)
            continue

        ### ignore favicon request
        if serverRecv == b'':
            continue

        print("\r\n" + serverRecv.decode())
        path = get_requested_file(serverRecv)
        filename = path[1:]

        ### check HTTP method
        if get_HTTP_method(serverRecv) != 'GET':
            print('Cannot {} {}'.format(get_HTTP_method(serverRecv), path))
            continue
        # hostName, hostPort = getHostandPort(serverRecv)

        ### check file path
        if not os.path.exists(filename):
            status_code = 404
            connection_socket.send(get_response_msg(status_code))
            print('Server Error : No such file {}!'.format(path))
        else:
            status_code = 200
            data_transferred = 0
            content_length = os.path.getsize(filename)
            connection_socket.send(get_response_msg(status_code, content_length))
            with open(filename, 'rb') as f:
                data = f.read(BUF_SIZE)
                while data:
                    try:
                        data_transferred += connection_socket.send(data)
                        data = f.read(BUF_SIZE)
                    except Exception as e:
                        print(e, "Error while sending data")
                        break
            print('finish {} {}'.format(data_transferred, content_length))
        connection_socket.close()
    server_socket.close()


if __name__ == '__main__':
    print('Student ID : 20165149')
    print('Name : Taeyoung Kwak')
    main(int(sys.argv[1]))
