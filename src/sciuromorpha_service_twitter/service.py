# eventlet monkey patch for nameko service startup.
import eventlet

eventlet.monkey_patch()  # noqa (code before rest of imports)

import sys
import signal
import errno
from nameko.runners import ServiceRunner

from .config import config
from .api.twitter import Twitter


def create_runner() -> ServiceRunner:
    runner = ServiceRunner(config=config)
    runner.add_service(Twitter)

    return runner


def main() -> int:
    runner = create_runner()

    runner.start()

    def signal_handler(signum, frame):
        eventlet.spawn_n(runner.stop)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Kill cannot be handled.
    # signal.signal(signal.SIGKILL, signal_handler)

    # if the signal handler fires while eventlet is waiting on a socket,
    # the __main__ greenlet gets an OSError(4) "Interrupted system call".
    # This is a side-effect of the eventlet hub mechanism. To protect nameko
    # from seeing the exception, we wrap the runner.wait call in a greenlet
    # spawned here, so that we can catch (and silence) the exception.
    runnlet = eventlet.spawn(runner.wait)

    while True:
        try:
            runnlet.wait()
        except OSError as exc:
            if exc.errno == errno.EINTR:
                # this is the OSError(4) caused by the signalhandler.
                # ignore and go back to waiting on the runner
                continue
            raise
        except KeyboardInterrupt:
            print() # looks nicer with the ^C e.g. bash prints in the terminal
            try:
                runner.stop()
            except KeyboardInterrupt:
                print() # looks nicer with the ^C e.g. bash prints in the terminal
                runner.kill()
        else:
            # runner.wait completed
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
