from abc import ABCMeta, abstractmethod

ABC = ABCMeta("ABC", (object,), {"__slots__": ()})


class ConnectivityFlowInterface(ABC):
    @abstractmethod
    def apply_connectivity_changes(self, request):
        pass
