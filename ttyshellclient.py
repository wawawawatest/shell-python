#ient_bash.py
import socket
import sys
import termios
import tty
from os import path, popen
from sys import stdout


# import thread, deal with byte
if (sys.version_info.major == 2):
    def get_byte(s, encoding="UTF-8"):
        return str(bytearray(s, encoding))
    STDOUT = stdout
    import thread
else:
    def get_byte(s, encoding="UTF-8"):
        return bytes(s, encoding=encoding)
    STDOUT = stdout.buffer
    import _thread as thread

FD = None
OLD_SETTINGS = None

class _GetchUnix:
    def __call__(self):
        global FD, OLD_SETTINGS
        FD = sys.stdin.fileno()
        OLD_SETTINGS = termios.tcgetattr(FD)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(FD, termios.TCSADRAIN, OLD_SETTINGS)
        return ch


getch = _GetchUnix()

CONN_ONLINE = 1


def stdprint(message):
    stdout.write(message)
    stdout.flush()


def close_socket(talk, exit_code=0):
    import os
    global FD, OLD_SETTINGS, CONN_ONLINE
    CONN_ONLINE = 0
    talk.close()
    try:
        termios.tcsetattr(FD, termios.TCSADRAIN, OLD_SETTINGS)
    except TypeError:
        pass
    os.system("clear")
    os.system("reset")
    os._exit(exit_code)


def recv_daemon(conn):
    global CONN_ONLINE
    while CONN_ONLINE:
        try:
            tmp = conn.recv(16)
            if (tmp):
                STDOUT.write(tmp)
                stdout.flush()
            else:
                raise socket.error
        except socket.error:
            msg = "Connection close by socket.\n"
            stdprint(msg)
            close_socket(conn, 1)


def main(port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn.bind(('0.0.0.0', port))
    conn.listen(1)
    reset = True
    try:
        rows, columns = popen('stty size', 'r').read().split()
    except Exception:
        reset = False
    try:
        talk, addr = conn.accept()
        stdprint("Connect from %s.\n" % addr[0])
        thread.start_new_thread(recv_daemon, (talk,))
        talk.send(get_byte("""script /dev/null && exit\n""", encoding='utf-8'))
        talk.send(get_byte("""reset\n""", encoding='utf-8'))
        if (reset):
            talk.send(get_byte("""resize -s %s %s > /dev/null\n""" % (rows, columns), encoding='utf-8'))
        while CONN_ONLINE:
            c = getch()
            if c:
                try:
                    talk.send(get_byte(c, encoding='utf-8'))
                except socket.error:
                    break
    except KeyboardInterrupt:
        pass
        # stdprint("Connection close by KeyboardInterrupt.\n")
    finally:
        stdprint("Connection close...\n")
        close_socket(conn, 0)


if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("usage:")
        print("      python %s [port]" % path.basename(sys.argv[0]))
        exit(2)
    main(int(sys.argv[1]))
