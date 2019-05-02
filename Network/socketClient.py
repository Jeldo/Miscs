from socket import *

BUF_SIZE = 512


def parseHeader(data):
    '''
    :param data: receive data from server and separate it into header and body
    :return: tuple(header, body)
    '''
    httpHeaderDelimeter = b'\r\n\r\n'
    try:
        index = data.index(httpHeaderDelimeter)
    except:
        return data, bytes()
    else:
        index += len(httpHeaderDelimeter)
        return data[:index], data[index:]


def getContentLength(header):
    '''
    :param header: decode header to string and parse header
    :return: int(content length)
    '''
    contentLengthField = 'Content-Length'
    header = header.decode()
    for line in header.split('\r\n'):
        if contentLengthField in line:
            return int(line[len(contentLengthField) + 1:])
    return 0


def getStatusCode(header):
    '''
    :param header: decode header to string and parse header
    :return: status code // ex) 100, 404
    '''
    header = header.decode()
    for line in header.split('\r\n'):
        if 'HTTP' in line:
            return int(line.split()[1])
    return 0


def getStatusMsg(header):
    '''
    :param header: decode header to string and parse header
    :return: status message // ex) NOT FOUND
    '''
    header = header.decode()
    for line in header.split('\r\n'):
        if 'HTTP' in line:
            return ' '.join(line.split()[2:])
    return ''


# ex) wget netapp.cs.kookmin.ac.kr 80 /web/member/palladio.JPG
def main():
    while True:
        cmd = input("Input Your Command: ")

        ### Parse and handle command
        if cmd == ' ' or cmd is None:
            continue
        elif cmd[:4] == 'quit' or cmd[:4] == 'QUIT':
            exit(0)
        if cmd.split() == []:
            continue
        cmd = cmd.split()
        webCmd = cmd[0]
        if webCmd != 'wget':
            print("Wrong command %s" % webCmd)
            continue
        hostname, pnum, filename = cmd[1:4]
        fname = filename.split('/')[-1]

        ### Handle getaddrinfo
        try:
            getaddrinfo(hostname, int(pnum))
        except:
            print(hostname, ": unknown host")
            print("cannot connect to server {} {}".format(hostname, pnum))
            continue
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((hostname, int(pnum)))

        ### Send GET request to server and receive response
        httpGETReq = "GET {} HTTP/1.0\r\nHost: {}\r\nUser-agent: HW1/1.0\r\nID: 20165149\r\nName: Taeyoung Kwak\r\nConnection: Close\r\n\r\n".format(
            filename, hostname)
        clientSocket.send(httpGETReq.encode())
        res = clientSocket.recv(BUF_SIZE)
        header, data = parseHeader(res)

        ### Handle via statuscode
        statusCode = getStatusCode(header)
        if statusCode != 200:
            print(statusCode, getStatusMsg(header))
            continue

        ### Get content length
        contentLength = getContentLength(header)
        print("Total Size {} bytes".format(contentLength))

        ### Download data
        dataTransferred = 0
        if not data:
            print("File [{}] doesn't exist or network error".format(fname))
            exit(0)
        f = open(fname, 'wb')
        try:
            count = 1
            while data:
                f.write(data)
                dataTransferred += len(data)
                data = clientSocket.recv(BUF_SIZE)
                if int(dataTransferred / contentLength * 100) >= count * 10:
                    print('Current Downloading {}/{} (bytes) {} %'.format(dataTransferred, contentLength,
                                                                          int(dataTransferred / contentLength * 100)))
                    count += 1
        except Exception as e:
            print(e)
        f.close()
        print("Download Complete: {}, {}/{}".format(fname, dataTransferred, contentLength))
        clientSocket.close()

if __name__=='__main__':
    main()