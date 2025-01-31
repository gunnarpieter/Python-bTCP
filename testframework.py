import unittest
import socket
import time
import sys
import threading
import filecmp

import ctypes

timeout=100
winsize=100
intf="lo"
netem_add="sudo tc qdisc add dev {} root netem".format(intf)
netem_change="sudo tc qdisc change dev {} root netem {}".format(intf,"{}")
netem_del="sudo tc qdisc del dev {} root netem".format(intf)

t = None
number = -1

"""run command and retrieve output"""
def run_command_with_output(command, input=None, cwd=None, shell=True):
    import subprocess
    try:
      process = subprocess.Popen(command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as inst:
      print("problem running command : \n   ", str(command))

    [stdoutdata, stderrdata]=process.communicate(input)  # no pipes set for stdin/stdout/stdout streams so does effectively only just wait for process ends  (same as process.wait()

    if process.returncode:
      print(stderrdata)
      print("problem running command : \n   ", str(command), " ",process.returncode)

    return stdoutdata

"""run command with no output piping"""
def run_command(command,cwd=None, shell=True):
    import subprocess
    process = None
    try:
        process = subprocess.Popen(command, shell=shell, cwd=cwd)
        print(str(process))
    except Exception as inst:
        print("1. problem running command : \n   ", str(command), "\n problem : ", str(inst))

    process.communicate()  # wait for the process to end

    if process.returncode:
        print("2. problem running command : \n   ", str(command), " ", process.returncode)

def doTheRest(number):
    input = "test/s.txt"
    run_command("python3 bTCP_client.py -i "+input + " -w "+str(winsize) + " -t " + str(timeout) + " > clientout/"+number)
    t.join()
    time.sleep(2)
    if not filecmp.cmp("testout/out"+number,input):
        print("Files are not the same")
        raise Exception(input+" is not the same as testout/"+number)
    else:
        print("Files are the same",input,"== testout/"+number)


class TestbTCPFramework(unittest.TestCase):
    """Test cases for bTCP"""

    def setUp(self):
        """Prepare for testing"""
        # default netem rule (does nothing)
        run_command(netem_add)
        # launch localhost server
        global t
        global number
        number+=1
        print("starting server with number ", number)
        t = threading.Thread(target=run_command, name="Server" , args=("python3 bTCP_server.py -w " + str(winsize) + " -t " + str(timeout) + " -o testout/out"+str(number) + " > serverout/"+str(number),))
        #t = thread_with_kill("Server")
        t.start()


    def tearDown(self):
        """Clean up after testing"""
        # clean the environment
        run_command(netem_del)
        # close server
        threads = threading.enumerate()
        for thread in threads:
            if thread.getName()=="Server":
                #thread.raise_exception()
                #thread.join()
                print("tried closing")

        #Done works
    def test_ideal_network(self):
        """reliability over an ideal framework"""
        # setup environment (nothing to set)
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nIdeal network:",number)
        doTheRest(str(number))
        #Done works
    def test_flipping_network(self):
        """reliability over network with bit flips
        (which sometimes results in lower layer packet loss)"""
        # setup environment
        run_command(netem_change.format("corrupt 1%"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nFlipping the network:",number)
        doTheRest(str(number))
        #Done works
    def test_duplicates_network(self):
        """reliability over network with duplicate packets"""
        # setup environment
        run_command(netem_change.format("duplicate 10%"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nDuplicate network:",number)
        doTheRest(str(number))
        #works only if the server starts corretly before everything else. Or so i tink
        #does not seem to work
    def test_lossy_network(self):
        """reliability over network with packet loss"""
        # setup environment
        run_command(netem_change.format("loss 10% 25%"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nLossy network:",number)
        doTheRest(str(number))
        #Done works
    def test_reordering_network(self):
        """reliability over network with packet reordering"""
        # setup environment
        run_command(netem_change.format("delay 20ms reorder 25% 50%"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nReordering network:",number)
        doTheRest(str(number))
        #DONE WORKS
    def test_delayed_network(self):
        """reliability over network with delay relative to the timeout value"""
        # setup environment
        run_command(netem_change.format("delay "+str(timeout)+"ms 20ms"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nTimeout network:",number)
        doTheRest(str(number))
     #Done works
    def test_allbad_network(self):
        """reliability over network with all of the above problems"""
        # setup environment
        run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 20ms reorder 25% 50%"))
        # launch localhost client connecting to server
        # client sends content to server
        # server receives content from client
        # content received by server matches the content sent by client
        global number
        print("\n\nAll network:",number)
        doTheRest(str(number))

#    def test_command(self):
#        #command=['dir','.']
#        out = run_command_with_output("dir .")
#        print(out)


if __name__ == "__main__":
    # Parse command line arguments
    print("#"*83)
    print("Keep in mind that a timeout test will take a long time when using a large testcase.")
    print("Next to that runtime is slower due to print statements to output files.")
    print("#"*83)
    import argparse
    parser = argparse.ArgumentParser(description="bTCP tests")
    parser.add_argument("-w", "--window", help="Define bTCP window size used", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define the timeout value used (ms)", type=int, default=timeout)
    args, extra = parser.parse_known_args()
    timeout = args.timeout
    winsize = args.window

    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()
