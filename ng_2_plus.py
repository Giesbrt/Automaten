import multiprocessing
from multiprocessing import shared_memory, Lock
import struct


class MP_TYPE:
    PARENT = 0
    CHILD = 1


class SharedStruct:
    def __init__(self, struct_format, create=False, shm_name=None):
        """
        Initialize a shared memory structure.

        :param struct_format: struct format string (e.g., 'iif' for int, int, float).
        :param create: Whether to create a new shared memory segment.
        :param shm_name: Name of the shared memory segment to connect to (if not creating).
        """
        self.struct_format = struct_format
        self.struct_size = struct.calcsize(struct_format)
        self.lock = Lock()

        if create:
            # Create new shared memory segment
            self.shm = shared_memory.SharedMemory(create=True, size=self.struct_size)
        else:
            # Attach to an existing shared memory segment
            if shm_name is None:
                raise ValueError("shm_name must be provided when create=False")
            self.shm = shared_memory.SharedMemory(name=shm_name)

        self.name = self.shm.name  # Store the shared memory name for reference

    def set_data(self, *values):
        """
        Set data in the shared memory structure.

        :param values: Values to set, matching the struct format.
        """
        if len(values) != len(self.struct_format.replace(' ', '')):
            raise ValueError("Number of values must match the struct format")

        with self.lock:
            packed_data = struct.pack(self.struct_format, *values)
            self.shm.buf[:self.struct_size] = packed_data

    def get_data(self):
        """
        Get data from the shared memory structure.

        :return: Tuple of values unpacked from the shared memory.
        """
        with self.lock:
            packed_data = self.shm.buf[:self.struct_size]
            return struct.unpack(self.struct_format, packed_data)

    def close(self):
        """
        Close the shared memory segment.
        """
        self.shm.close()

    def unlink(self):
        """
        Unlink the shared memory segment (only call this if you own the memory).
        """
        self.shm.unlink()


def child_process(shm_name):
    shared_struct_child = SharedStruct('iif', create=False, shm_name=shm_name)
    print("Child initial data:", shared_struct_child.get_data())
    shared_struct_child.set_data(84, 14, 6.28)
    print("Child updated data:", shared_struct_child.get_data())
    shared_struct_child.close()


if __name__ == "__main__":
    # Define a struct with two integers and one float
    struct_format = 'iif'

    # Create a shared struct
    shared_struct = SharedStruct(struct_format, create=True)

    # Set initial data
    shared_struct.set_data(42, 7, 3.14)
    print("Parent initial data:", shared_struct.get_data())

    # Pass the shared memory name to a child process

    process = multiprocessing.Process(target=child_process, args=(shared_struct.name,))
    process.start()
    process.join()

    # Check updated data in the parent process
    print("Parent updated data:", shared_struct.get_data())

    # Clean up
    shared_struct.close()
    shared_struct.unlink()
