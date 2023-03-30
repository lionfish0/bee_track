from multiprocessing import Queue, Value
from multiprocessing import sharedctypes
from threading import Thread

class Configurable():
    def __init__(self,message_queue):
        self.config_queue = Queue()
        self.message_queue = message_queue
        t = Thread(target=self.config_worker)
        t.start()
        
    def config_worker(self):
        """this method is a worker that waits for the config queue"""
        while True:
            command = self.config_queue.get()
            

            if command[0]=='get':
                if len(command)!=2: 
                    self.message_queue.put("Wrong number of items in get call")
                    continue
            if command[0]=='set':
                if len(command)!=3:            
                    self.message_queue.put("Wrong number of items in set call")
                    continue
            if (command[0]!='get') and (command[0]!='set'):
                    self.message_queue.put("Use set or get")
                    continue
            if not hasattr(self,command[1]):
                    print(self.index)
                    self.message_queue.put("%s not available in this class." % command[1])
                    continue
            
            att = getattr(self,command[1])
            if type(att)==sharedctypes.Synchronized:
                v = att.value
            else:
                v = att
            if command[0]=='get':              
                self.message_queue.put("Value of %s is %s" % (command[1],v))
                continue
            if command[0]=='set': 
                try:
                    if type(att)==sharedctypes.Synchronized:
                        getattr(self,command[1]).value = type(v)(command[2])
                    else:
                        setattr(self,command[1],type(v)(command[2]))

                    self.message_queue.put("Set %s to %s" % (command[1],command[2]))

                except Exception as e:
                    self.message_queue.put("Failed to set:" + str(e))
            
