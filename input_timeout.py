import threading
import queue
import time


def get_input(message, channel):
    response = input(message)
    channel.put(response)


channel = queue.Queue()


def input_with_timeout(message, timeout):
    message = message + " [{} sec timeout] ".format(timeout)
    thread = threading.Thread(target=get_input, args=(message, channel))
    # by setting this as a daemon thread, python won't wait for it to complete
    thread.daemon = True
    thread.start()

    try:
        response = channel.get(True, timeout)
        return response
    except queue.Empty:
        pass
    return None


if __name__ == "__main__":
    a = input_with_timeout("Commands:", 5)
    time.sleep(3)
    print(a)