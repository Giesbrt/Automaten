from multiprocessing import Process, shared_memory
import numpy as np


def worker(shared_mem_name, shape, dtype):
    # Attach to the shared memory segment in the child process
    shm = shared_memory.SharedMemory(name=shared_mem_name)
    # Reconstruct the NumPy array from the shared memory buffer
    shared_array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    # Modify the array
    shared_array += 1  # Increment all elements
    shm.close()  # Close the shared memory in the child process


if __name__ == "__main__":
    # Create a NumPy array to share
    array = np.array([1, 2, 3, 4], dtype=np.int32)

    # Create a shared memory segment
    shm = shared_memory.SharedMemory(create=True, size=array.nbytes)

    # Copy the data into the shared memory buffer
    shared_array = np.ndarray(array.shape, dtype=array.dtype, buffer=shm.buf)
    shared_array[:] = array[:]

    # Spawn processes to modify the shared memory
    processes = [Process(target=worker, args=(shm.name, array.shape, array.dtype)) for _ in range(2)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    # Read the modified shared array
    print(shared_array)  # Output: [3, 4, 5, 6] (incremented twice)

    shm.close()  # Close the shared memory in the parent process
    shm.unlink()  # Unlink the shared memory to release resources
